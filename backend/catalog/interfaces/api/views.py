from uuid import UUID

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.interfaces.api.permissions import IsManager
from catalog.application.commands import (
    CreateCategoryCommand,
    CreateProductCommand,
    DeactivateCategoryCommand,
    DeactivateProductCommand,
    UpdateCategoryCommand,
    UpdateProductCommand,
)
from catalog.application.use_cases import (
    CreateCategoryUseCase,
    CreateProductUseCase,
    DeactivateCategoryUseCase,
    DeactivateProductUseCase,
    ListCategoriesUseCase,
    UpdateCategoryUseCase,
    UpdateProductUseCase,
)
from catalog.infrastructure.adapters import InventoryOpeningStockAdapter
from catalog.infrastructure.repository import DjangoCategoryRepository, DjangoProductRepository
from catalog.interfaces.api.serializers import (
    CategorySerializer,
    CreateCategorySerializer,
    CreateProductSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    UpdateCategorySerializer,
    UpdateProductSerializer,
)
from shared.domain.clock import SystemClock
from shared.domain.money import Money
from shared.infrastructure.audit import build_audit_recorder


class ProductListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsManager()]
        return [IsAuthenticated()]

    def get(self, request):
        repo = DjangoProductRepository()
        query = request.query_params.get("q", "")
        category_id = request.query_params.get("category_id")
        active_only = request.query_params.get("active_only", "true").lower() == "true"

        if query:
            products = repo.search(
                query,
                active_only=active_only,
                category_id=UUID(category_id) if category_id else None,
            )
        else:
            products = repo.list_products(
                active_only=active_only, category_id=UUID(category_id) if category_id else None
            )

        return Response(ProductListSerializer(products, many=True).data)

    def post(self, request):
        serializer = CreateProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = CreateProductUseCase(
            DjangoProductRepository(),
            SystemClock(),
            InventoryOpeningStockAdapter(),
            build_audit_recorder(),
        )
        try:
            product = use_case.execute(
                CreateProductCommand(
                    name=data["name"],
                    sku=data["sku"],
                    selling_price=Money(data["selling_price"]),
                    buying_cost=Money(data["buying_cost"]),
                    description=data.get("description", ""),
                    barcode=data.get("barcode"),
                    category_id=data.get("category_id"),
                    minimum_stock_level=data.get("minimum_stock_level", 0),
                    image_url=data.get("image_url"),
                    opening_stock=data.get("opening_stock", 0),
                    user_id=request.user.id if request.user.is_authenticated else None,
                )
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ProductDetailSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductByBarcodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        barcode = request.query_params.get("barcode", "").strip()
        if not barcode:
            return Response(
                {"detail": "A barcode query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        repo = DjangoProductRepository()
        product = repo.get_by_barcode(barcode)
        if product is None or not product.is_active:
            return Response(
                {"detail": "No active product matches that barcode."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ProductDetailSerializer(product).data)


class ProductDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsManager()]
        return [IsAuthenticated()]

    def get(self, request, product_id):
        repo = DjangoProductRepository()
        product = repo.get_by_id(product_id)
        if product is None:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductDetailSerializer(product).data)

    def patch(self, request, product_id):
        serializer = UpdateProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = UpdateProductUseCase(
            DjangoProductRepository(), SystemClock(), build_audit_recorder()
        )
        try:
            product = use_case.execute(
                UpdateProductCommand(
                    product_id=product_id,
                    name=data.get("name"),
                    sku=data.get("sku"),
                    description=data.get("description"),
                    barcode=data.get("barcode"),
                    category_id=data.get("category_id"),
                    selling_price=Money(data["selling_price"]) if "selling_price" in data else None,
                    buying_cost=Money(data["buying_cost"]) if "buying_cost" in data else None,
                    minimum_stock_level=data.get("minimum_stock_level"),
                    image_url=data.get("image_url"),
                    is_active=data.get("is_active"),
                    user_id=request.user.id if request.user.is_authenticated else None,
                )
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ProductDetailSerializer(product).data)

    def delete(self, request, product_id):
        use_case = DeactivateProductUseCase(
            DjangoProductRepository(), SystemClock(), build_audit_recorder()
        )
        try:
            use_case.execute(
                DeactivateProductCommand(
                    product_id=product_id,
                    user_id=request.user.id if request.user.is_authenticated else None,
                )
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsManager()]
        return [IsAuthenticated()]

    def get(self, request):
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        use_case = ListCategoriesUseCase(DjangoCategoryRepository())
        categories = use_case.execute(active_only=active_only)
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CreateCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = CreateCategoryUseCase(DjangoCategoryRepository(), build_audit_recorder())
        category = use_case.execute(
            CreateCategoryCommand(
                name=data["name"],
                description=data.get("description", ""),
                parent_id=data.get("parent_id"),
                user_id=request.user.id if request.user.is_authenticated else None,
            )
        )
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class CategoryDetailView(APIView):
    permission_classes = [IsManager]

    def patch(self, request, category_id):
        serializer = UpdateCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = UpdateCategoryUseCase(DjangoCategoryRepository(), build_audit_recorder())
        try:
            category = use_case.execute(
                UpdateCategoryCommand(
                    category_id=category_id,
                    name=data.get("name"),
                    description=data.get("description"),
                    parent_id=data.get("parent_id"),
                    parent_set="parent_id" in data,
                    is_active=data.get("is_active"),
                    user_id=request.user.id if request.user.is_authenticated else None,
                )
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CategorySerializer(category).data)

    def delete(self, request, category_id):
        use_case = DeactivateCategoryUseCase(DjangoCategoryRepository(), build_audit_recorder())
        try:
            use_case.execute(
                DeactivateCategoryCommand(
                    category_id=category_id,
                    user_id=request.user.id if request.user.is_authenticated else None,
                )
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
