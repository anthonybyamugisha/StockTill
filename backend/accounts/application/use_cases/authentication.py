from accounts.domain.entities import User
from accounts.domain.errors import InvalidCredentialsError
from accounts.domain.password import PasswordHasher
from accounts.domain.repository import UserRepository
from shared.application.audit import AuditPort, NullAuditPort


class AuthenticateUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        audit: AuditPort | None = None,
    ):
        self._repo = user_repository
        self._hasher = password_hasher
        self._audit = audit or NullAuditPort()

    def execute(self, email: str, password: str) -> User:
        user = self._repo.get_by_email(email)

        if user is None or not user.check_password(password, self._hasher):
            if user is not None:
                user.register_failed_login()
                self._repo.save(user)
            self._audit.record(
                user_id=user.id if user is not None else None,
                action="auth.login_failed",
                entity_type="user",
                entity_id=str(user.id) if user is not None else email,
                after={"email": email},
            )
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            self._audit.record(
                user_id=user.id,
                action="auth.login_blocked",
                entity_type="user",
                entity_id=str(user.id),
                after={"email": user.email, "reason": "deactivated"},
            )
            raise InvalidCredentialsError("Account deactivated")

        if user.is_locked():
            locked_until = user.locked_until
            detail = locked_until.isoformat() if locked_until is not None else ""
            self._audit.record(
                user_id=user.id,
                action="auth.login_blocked",
                entity_type="user",
                entity_id=str(user.id),
                after={"email": user.email, "reason": "locked"},
            )
            raise InvalidCredentialsError(f"Account locked. Try again after {detail}")

        first_login = user.is_first_login
        if first_login and not user.is_superuser:
            user.require_password_change()

        user.register_successful_login()
        self._repo.save(user)
        if first_login and user.must_change_password:
            self._audit.record(
                user_id=user.id,
                action="auth.first_login",
                entity_type="user",
                entity_id=str(user.id),
                after={"email": user.email, "password_change_required": True},
            )
        self._audit.record(
            user_id=user.id,
            action="auth.login",
            entity_type="user",
            entity_id=str(user.id),
            after={"email": user.email},
        )
        return user
