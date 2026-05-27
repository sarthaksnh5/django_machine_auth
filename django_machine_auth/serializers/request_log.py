from rest_framework import serializers

from django_machine_auth.models import APIKeyRequestLog


class MachineAPIKeyRequestLogListSerializer(serializers.ModelSerializer):
    api_key_name = serializers.CharField(source="api_key.name", read_only=True, allow_null=True)

    class Meta:
        model = APIKeyRequestLog
        fields = [
            "id",
            "api_key_id",
            "api_key_name",
            "user_id",
            "url",
            "method",
            "status_code",
            "duration",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields


class MachineAPIKeyRequestLogDetailSerializer(serializers.ModelSerializer):
    api_key_name = serializers.CharField(source="api_key.name", read_only=True, allow_null=True)

    class Meta:
        model = APIKeyRequestLog
        fields = [
            "id",
            "api_key_id",
            "api_key_name",
            "user_id",
            "url",
            "method",
            "headers",
            "request_body",
            "response_body",
            "status_code",
            "duration",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields
