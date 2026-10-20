from accounts.application.commands import ChangePasswordCommand
from accounts.domain.entities import User
from accounts.domain.errors import InvalidCurrentPasswordError
from accounts.domain.password import PasswordHasher, validate_password_strength
from accounts.domain.repository import UserRepository


class ChangePasswordUseCase:
    def __init__(self, user_repository: UserRepository, password_hasher: PasswordHasher):
        self._repo = user_repository
        self._hasher = password_hasher

    def execute(self, command: ChangePasswordCommand) -> User:
        user = self._repo.get_by_id(command.user_id)
        if user is None:
            raise ValueError("User not found")

        if not user.check_password(command.current_password, self._hasher):
            raise InvalidCurrentPasswordError("Current password is incorrect")

        validate_password_strength(command.new_password)
        user.change_password(command.new_password, self._hasher)
        self._repo.save(user)
        return user
