from accounts.application.commands import (
    CreateUserCommand,
    DeactivateUserCommand,
    UpdateUserCommand,
)
from accounts.domain.entities import User
from accounts.domain.password import PasswordHasher
from accounts.domain.repository import UserRepository
from shared.application.audit import AuditPort, NullAuditPort


class CreateUserUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        audit: AuditPort | None = None,
    ):
        self._repo = user_repository
        self._hasher = password_hasher
        self._audit = audit or NullAuditPort()

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
        user.require_password_change()
        self._repo.save(user)
        self._audit.record(
            user_id=command.actor_id,
            action="user.created",
            entity_type="user",
            entity_id=str(user.id),
            after={
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
            },
        )
        return user


class UpdateUserUseCase:
    def __init__(self, user_repository: UserRepository, audit: AuditPort | None = None):
        self._repo = user_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: UpdateUserCommand) -> User:
        user = self._repo.get_by_id(command.user_id)
        if user is None:
            raise ValueError("User not found")

        before = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
        }

        if command.first_name is not None:
            user.first_name = command.first_name
        if command.last_name is not None:
            user.last_name = command.last_name
        if command.role is not None:
            user.role = command.role

        self._repo.save(user)

        after = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
        }
        changed = {key: value for key, value in after.items() if value != before[key]}
        if changed:
            self._audit.record(
                user_id=command.actor_id,
                action="user.updated",
                entity_type="user",
                entity_id=str(user.id),
                before={key: before[key] for key in changed},
                after=changed,
            )
            if "role" in changed:
                self._audit.record(
                    user_id=command.actor_id,
                    action="user.role_changed",
                    entity_type="user",
                    entity_id=str(user.id),
                    before={"role": before["role"]},
                    after={"role": after["role"]},
                )
        return user


class DeactivateUserUseCase:
    def __init__(self, user_repository: UserRepository, audit: AuditPort | None = None):
        self._repo = user_repository
        self._audit = audit or NullAuditPort()

    def execute(self, command: DeactivateUserCommand) -> User:
        user = self._repo.get_by_id(command.user_id)
        if user is None:
            raise ValueError("User not found")

        user.is_active = False
        self._repo.save(user)
        self._audit.record(
            user_id=command.actor_id,
            action="user.deactivated",
            entity_type="user",
            entity_id=str(user.id),
            before={"is_active": True, "email": user.email},
            after={"is_active": False},
        )
        return user
