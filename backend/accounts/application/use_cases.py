from accounts.application.commands import (
    CreateUserCommand,
    DeactivateUserCommand,
    UpdateUserCommand,
)
from accounts.domain.entities import User
from accounts.domain.errors import InvalidCredentialsError
from accounts.domain.password import PasswordHasher
from accounts.domain.repository import UserRepository


class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher):
        self._repo = user_repository
        self._hasher = password_hasher

    def execute(self, command: CreateUserCommand) -> User:
        if self._repo.email_exists(command.email):
            raise ValueError("Email already registered")

        user = User(
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name,
            role=command.role,
        )
        user.set_password(command.password, self._hasher)
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


class AuthenticateUserUseCase:
    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher):
        self._repo = user_repository
        self._hasher = password_hasher

    def execute(self, email: str, password: str) -> User:
        user = self._repo.get_by_email(email)

        if user is None or not user.check_password(password, self._hasher):
            if user is not None:
                user.register_failed_login()
                self._repo.save(user)
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InvalidCredentialsError("Account deactivated")

        if user.is_locked():
            locked_until = user.locked_until
            detail = locked_until.isoformat() if locked_until is not None else ""
            raise InvalidCredentialsError(f"Account locked. Try again after {detail}")

        user.register_successful_login()
        self._repo.save(user)
        return user
