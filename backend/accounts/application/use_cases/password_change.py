from accounts.application.commands import ChangePasswordCommand
from accounts.domain.entities import User
from accounts.domain.errors import InvalidCurrentPasswordError, WeakPasswordError
from accounts.domain.password import PasswordHasher, validate_password_strength
from accounts.domain.repository import UserRepository
from shared.application.audit import AuditPort, NullAuditPort


class ChangePasswordUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        audit: AuditPort | None = None,
    ):
        self._repo = user_repository
        self._hasher = password_hasher
        self._audit = audit or NullAuditPort()

    def execute(self, command: ChangePasswordCommand) -> User:
        user = self._repo.get_by_id(command.user_id)
        if user is None:
            raise ValueError("User not found")

        if not user.check_password(command.current_password, self._hasher):
            raise InvalidCurrentPasswordError("Current password is incorrect")

        validate_password_strength(command.new_password)
        if command.new_password == command.current_password:
            raise WeakPasswordError("New password must be different from the current password")
        user.change_password(command.new_password, self._hasher)
        self._repo.save(user)
        self._audit.record(
            user_id=user.id,
            action="auth.password_changed",
            entity_type="user",
            entity_id=str(user.id),
            after={"email": user.email},
        )
        return user
