from uuid import UUID

from accounts.domain.entities import Role, User
from accounts.domain.repository import UserRepository
from accounts.infrastructure.models import UserModel


class DjangoUserRepository(UserRepository):
    def get_by_id(self, user_id: UUID) -> User | None:
        try:
            m = UserModel.objects.get(id=user_id)
            return self._to_domain(m)
        except UserModel.DoesNotExist:
            return None

    def get_by_email(self, email: str) -> User | None:
        try:
            m = UserModel.objects.get(email__iexact=email)
            return self._to_domain(m)
        except UserModel.DoesNotExist:
            return None

    def list_users(self, *, active_only: bool = False) -> list[User]:
        qs = UserModel.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        return [self._to_domain(m) for m in qs]

    def save(self, user: User) -> None:
        UserModel.objects.update_or_create(
            id=user.id,
            defaults={
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "is_active": user.is_active,
                "last_login": user.last_login,
                "failed_login_attempts": user.failed_login_attempts,
                "locked_until": user.locked_until,
                "must_change_password": user.must_change_password,
                "password": user.password_hash,
            },
        )

    def email_exists(self, email: str) -> bool:
        return UserModel.objects.filter(email__iexact=email).exists()

    def _to_domain(self, m: UserModel) -> User:
        return User(
            id=m.id,
            email=m.email,
            first_name=m.first_name,
            last_name=m.last_name,
            role=Role(m.role),
            is_active=m.is_active,
            is_superuser=m.is_superuser,
            last_login=m.last_login,
            failed_login_attempts=m.failed_login_attempts,
            locked_until=m.locked_until,
            must_change_password=m.must_change_password,
            password_hash=m.password,
        )
