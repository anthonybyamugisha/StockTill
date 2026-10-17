from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.application.commands import CreateUserCommand
from accounts.application.use_cases import CreateUserUseCase
from accounts.domain.entities import Role
from accounts.infrastructure.repository import DjangoUserRepository
from accounts.interfaces.api.serializers import CreateUserSerializer, UserSerializer


class UserListCreateView(APIView):
    def get(self, request):
        repo = DjangoUserRepository()
        users = repo.list_users(active_only=True)
        return Response(UserSerializer(users, many=True).data)

    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        use_case = CreateUserUseCase(DjangoUserRepository())
        user = use_case.execute(
            CreateUserCommand(
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=Role(data["role"]),
                password=data["password"],
            )
        )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
