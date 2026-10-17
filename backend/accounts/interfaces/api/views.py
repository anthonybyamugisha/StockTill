from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.application.commands import (
    CreateUserCommand,
    DeactivateUserCommand,
    UpdateUserCommand,
)
from accounts.application.use_cases import (
    AuthenticateUserUseCase,
    CreateUserUseCase,
    DeactivateUserUseCase,
    UpdateUserUseCase,
)
from accounts.domain.entities import Role
from accounts.infrastructure.password_hasher import DjangoPasswordHasher
from accounts.infrastructure.repository import DjangoUserRepository
from accounts.interfaces.api.permissions import IsAdmin
from accounts.interfaces.api.serializers import (
    CreateUserSerializer,
    LoginSerializer,
    UserSerializer,
)


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
        use_case = CreateUserUseCase(DjangoUserRepository(), DjangoPasswordHasher())
        try:
            user = use_case.execute(
                CreateUserCommand(
                    email=data["email"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    role=Role(data["role"]),
                    password=data["password"],
                )
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


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

        use_case = UpdateUserUseCase(repo)
        updated = use_case.execute(
            UpdateUserCommand(
                user_id=user_id,
                first_name=request.data.get("first_name"),
                last_name=request.data.get("last_name"),
                role=Role(request.data["role"]) if "role" in request.data else None,
            )
        )
        return Response(UserSerializer(updated).data)

    def delete(self, request, user_id):
        repo = DjangoUserRepository()
        user = repo.get_by_id(user_id)
        if user is None:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        use_case = DeactivateUserUseCase(repo)
        use_case.execute(DeactivateUserCommand(user_id=user_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        use_case = AuthenticateUserUseCase(DjangoUserRepository(), DjangoPasswordHasher())
        try:
            user = use_case.execute(data["email"], data["password"])
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        from accounts.infrastructure.models import UserModel

        model = UserModel.objects.get(id=user.id)
        django_login(request, model)
        return Response(UserSerializer(model).data)


class LogoutView(APIView):
    permission_classes = []

    def post(self, request):
        django_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = []

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(UserSerializer(request.user).data)


class AuditLogView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        from accounts.infrastructure.models import AuditLogModel

        entries = AuditLogModel.objects.all().order_by("-timestamp")[:100]
        return Response(
            [
                {
                    "id": str(e.id),
                    "user_id": str(e.user_id) if e.user_id else None,
                    "action": e.action,
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "before": e.before,
                    "after": e.after,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in entries
            ]
        )
