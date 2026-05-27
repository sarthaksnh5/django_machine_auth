from rest_framework import serializers

from django_machine_auth.models import MachinePermission


class MachinePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachinePermission
        fields = ["id", "module", "permission", "label"]
