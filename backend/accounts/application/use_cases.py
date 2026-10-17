from accounts.application.commands import CreateUserCommand, DeactivateUserCommand, UpdateUserCommand
from accounts.domain.entities import User
from accounts.domain.repository import UserRepository


class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository

    def execute(self, command: CreateUserCommand) -> User:
        user = User(
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name,
            role=command.role,
        )
        self._repo.save(user)
        return user


class UpdateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository

    def execute(self, command: UpdateUserCommand) -> User:
        user = self._repo.get_by_id(command.user_id)
        if user is None:
            raise ValueError("User not found")
        if command.first_name is not None:
            user.first_name = command.first_name
        if command.last_name is not None:
            user.last_name = command.last_name
        if command.role is not None:
            user.role = command.role
        self._repo.save(user)
        return user


class DeactivateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self._repo = user_repository

    def execute(self, command: DeactivateUserCommand) -> User:
        user = self._repo.get_by_id(command.user_id)
        if user is None:
            raise ValueError("User not found")
        user.is_active = False
        self._repo.save(user)
        return user
