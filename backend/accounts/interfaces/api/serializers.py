from rest_framework import serializers

from accounts.domain.entities import Role, User
from accounts.domain.errors import WeakPasswordError
from accounts.domain.password import validate_password_strength


class UserSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    role = serializers.ChoiceField(choices=[r.value for r in Role])
    is_active = serializers.BooleanField(read_only=True)
    must_change_password = serializers.BooleanField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data):
        return User(**validated_data)


class CashierSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    role = serializers.ChoiceField(choices=[r.value for r in Role])
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_password(self, value: str) -> str:
        try:
            validate_password_strength(value)
        except WeakPasswordError as e:
            raise serializers.ValidationError(str(e)) from e
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)


class AuditLogSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user_id = serializers.UUIDField(allow_null=True)
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    action = serializers.CharField()
    entity_type = serializers.CharField()
    entity_id = serializers.CharField()
    before = serializers.JSONField(allow_null=True)
    after = serializers.JSONField(allow_null=True)
    timestamp = serializers.DateTimeField()

    def _user(self, obj):
        return self.context.get("users", {}).get(obj.user_id)

    def get_user_name(self, obj) -> str | None:
        user = self._user(obj)
        if user is None:
            return None
        return f"{user.first_name} {user.last_name}".strip() or user.email

    def get_user_email(self, obj) -> str | None:
        user = self._user(obj)
        return user.email if user is not None else None
