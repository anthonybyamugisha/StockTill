from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.application.commands import CreateProductCommand
from catalog.application.use_cases import CreateProductUseCase
from catalog.infrastructure.repository import DjangoProductRepository
from catalog.interfaces.api.serializers import CreateProductSerializer, ProductSerializer
from shared.domain.money import Money


class ProductListCreateView(APIView):
    def get(self, request):
        repo = DjangoProductRepository()
        products = repo.list_products()
        return Response(ProductSerializer(products, many=True).data)

    def post(self, request):
        serializer = CreateProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = CreateProductUseCase(DjangoProductRepository())
        product = use_case.execute(
            CreateProductCommand(
                name=data["name"],
                description=data.get("description", ""),
                sku=data["sku"],
                barcode=data.get("barcode"),
                category_id=data.get("category_id"),
                buying_cost=Money(data["buying_cost"]),
                selling_price=Money(data["selling_price"]),
                minimum_stock_level=data.get("minimum_stock_level", 0),
                image_url=data.get("image_url"),
            )
        )
        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)


class ProductSearchView(APIView):
    def get(self, request):
        query = request.query_params.get("q", "")
        repo = DjangoProductRepository()
        products = repo.search(query)
        return Response(ProductSerializer(products, many=True).data)
