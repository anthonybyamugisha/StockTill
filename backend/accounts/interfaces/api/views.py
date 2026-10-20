from uuid import UUID

from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import update_session_auth_hash
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.application.commands import (
    ChangePasswordCommand,
    CreateUserCommand,
    DeactivateUserCommand,
    UpdateUserCommand,
)
from accounts.application.use_cases import (
    AuthenticateUserUseCase,
    ChangePasswordUseCase,
    CreateUserUseCase,
    DeactivateUserUseCase,
    UpdateUserUseCase,
)
from accounts.domain.entities import Role
from accounts.domain.errors import DomainError
from accounts.infrastructure.audit_repository import DjangoAuditRepository
from accounts.infrastructure.models import UserModel
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from accounts.infrastructure.repository import DjangoUserRepository
from accounts.interfaces.api.permissions import IsAdmin, IsManager
from accounts.interfaces.api.serializers import (
    AuditLogSerializer,
    CashierSerializer,
    ChangePasswordSerializer,
    CreateUserSerializer,
    LoginSerializer,
    UserSerializer,
)
from shared.infrastructure.audit import build_audit_recorder


def _optional_uuid(value):
    try:
        return UUID(value) if value else None
    except (TypeError, ValueError):
        return None


class UserListCreateView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        repo = DjangoUserRepository()
        active_only = request.query_params.get("active_only", "true").lower() == "true"
        users = repo.list_users(active_only=active_only)
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = CreateUserUseCase(
            DjangoUserRepository(), DjangoPasswordHasher(), build_audit_recorder()
        )
        try:
            user = use_case.execute(
                CreateUserCommand(
                    email=data["email"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    role=Role(data["role"]),
                    password=data["password"],
                    actor_id=request.user.id if request.user.is_authenticated else None,
                )
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class CashierListView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        users = UserModel.objects.filter(role=Role.CASHIER.value, is_active=True).order_by(
            "first_name", "last_name"
        )
        return Response(CashierSerializer(users, many=True).data)


class UserDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, user_id):
        repo = DjangoUserRepository()
        user = repo.get_by_id(user_id)
        if user is None:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(user).data)

    def patch(self, request, user_id):
        repo = DjangoUserRepository()
        user = repo.get_by_id(user_id)
        if user is None:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        use_case = UpdateUserUseCase(repo, build_audit_recorder())
        updated = use_case.execute(
            UpdateUserCommand(
                user_id=user_id,
                first_name=request.data.get("first_name"),
                last_name=request.data.get("last_name"),
                role=Role(request.data["role"]) if "role" in request.data else None,
                actor_id=request.user.id if request.user.is_authenticated else None,
            )
        )
        return Response(UserSerializer(updated).data)

    def delete(self, request, user_id):
        repo = DjangoUserRepository()
        user = repo.get_by_id(user_id)
        if user is None:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        use_case = DeactivateUserUseCase(repo, build_audit_recorder())
        use_case.execute(
            DeactivateUserCommand(
                user_id=user_id,
                actor_id=request.user.id if request.user.is_authenticated else None,
            )
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = AuthenticateUserUseCase(
            DjangoUserRepository(), DjangoPasswordHasher(), build_audit_recorder()
        )
        try:
            user = use_case.execute(data["email"], data["password"])
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        model = UserModel.objects.get(id=user.id)
        django_login(request, model)
        return Response(UserSerializer(model).data)


class LogoutView(APIView):
    permission_classes = []

    def post(self, request):
        user_id = request.user.id if request.user.is_authenticated else None
        email = request.user.email if request.user.is_authenticated else None
        django_logout(request)
        if user_id is not None:
            build_audit_recorder().record(
                user_id=user_id,
                action="auth.logout",
                entity_type="user",
                entity_id=str(user_id),
                after={"email": email},
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = []

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = ChangePasswordUseCase(
            DjangoUserRepository(), DjangoPasswordHasher(), build_audit_recorder()
        )
        try:
            use_case.execute(
                ChangePasswordCommand(
                    user_id=request.user.id,
                    current_password=data["current_password"],
                    new_password=data["new_password"],
                )
            )
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        model = UserModel.objects.get(id=request.user.id)
        update_session_auth_hash(request, model)
        return Response(UserSerializer(model).data)


class AuditLogView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        entries = DjangoAuditRepository().list_entries(
            user_id=_optional_uuid(request.query_params.get("user_id")),
            entity_type=request.query_params.get("entity_type") or None,
            action=request.query_params.get("action") or None,
            date_from=request.query_params.get("date_from") or None,
            date_to=request.query_params.get("date_to") or None,
        )[:100]
        user_ids = {entry.user_id for entry in entries if entry.user_id is not None}
        users = {user.id: user for user in UserModel.objects.filter(id__in=user_ids)}
        return Response(AuditLogSerializer(entries, many=True, context={"users": users}).data)
