from rest_framework import serializers

from django_machine_auth.models import MachineAPIKey, MachinePermission
from django_machine_auth.utils.hashing import hash_api_key
from django_machine_auth.utils.key_generator import generate_api_key


def _validate_permissions_against_db(permissions):
    valid_permissions = set(
        MachinePermission.objects.values_list("permission", flat=True)  # pylint: disable=no-member
    )
    invalid = sorted({perm for perm in permissions if perm not in valid_permissions})
    if invalid:
        raise serializers.ValidationError(f"Invalid permissions: {', '.join(invalid)}")
    return permissions


class MachineAPIKeyCreateSerializer(serializers.ModelSerializer):
    raw_api_key = serializers.CharField(read_only=True)
    permissions = serializers.ListField(child=serializers.CharField(), allow_empty=False)

    class Meta:
        model = MachineAPIKey
        fields = [
            "id",
            "name",
            "user",
            "expires_at",
            "permissions",
            "is_active",
            "created_at",
            "raw_api_key",
        ]
        read_only_fields = ["id", "is_active", "created_at", "raw_api_key"]

    def validate_permissions(self, value):
        return _validate_permissions_against_db(value)

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.is_authenticated and not request.user.is_superuser:
            requested_user = attrs.get("user")
            if requested_user and requested_user != request.user:
                raise serializers.ValidationError(
                    {"user": "You can only create API keys for yourself."}
                )
            attrs["user"] = request.user
        return attrs

    def create(self, validated_data):
        raw_key = generate_api_key()
        permissions = validated_data.pop("permissions")
        obj = MachineAPIKey.objects.create(  # pylint: disable=no-member
            name=validated_data["name"],
            user=validated_data["user"],
            expires_at=validated_data.get("expires_at"),
            hashed_key=hash_api_key(raw_key),
            permissions=permissions,
            is_active=True,
        )
        obj.raw_api_key = raw_key
        return obj


class MachineAPIKeyListSerializer(serializers.ModelSerializer):
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = MachineAPIKey
        fields = [
            "id",
            "name",
            "user",
            "permissions",
            "expires_at",
            "is_active",
            "is_expired",
            "last_used_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MachineAPIKeyDetailSerializer(MachineAPIKeyListSerializer):
    class Meta(MachineAPIKeyListSerializer.Meta):
        fields = MachineAPIKeyListSerializer.Meta.fields


class MachineAPIKeyUpdateSerializer(serializers.ModelSerializer):
    permissions = serializers.ListField(child=serializers.CharField(), allow_empty=False, required=False)

    class Meta:
        model = MachineAPIKey
        fields = ["name", "permissions", "expires_at", "is_active"]

    def validate_permissions(self, value):
        return _validate_permissions_against_db(value)
