from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from django_machine_auth.utils.cache import invalidate_auth_payload


class MachineAPIKey(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="machine_api_keys")
    hashed_key = models.CharField(max_length=64, unique=True, db_index=True)
    permissions = models.JSONField(default=list)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())

    def clean(self):
        from django_machine_auth.models.permission import MachinePermission

        valid = set(MachinePermission.objects.values_list("permission", flat=True))
        invalid = [perm for perm in self.permissions if perm not in valid]
        if invalid:
            raise ValidationError({"permissions": f"Invalid permissions: {', '.join(sorted(invalid))}"})

    def save(self, *args, **kwargs):
        previous = None
        if self.pk:
            previous = (
                MachineAPIKey.objects.filter(pk=self.pk)
                .values("hashed_key", "permissions", "is_active", "expires_at")
                .first()
            )
        super().save(*args, **kwargs)
        if not previous:
            invalidate_auth_payload(self.hashed_key)
            return

        changed = (
            previous["permissions"] != self.permissions
            or previous["is_active"] != self.is_active
            or previous["expires_at"] != self.expires_at
            or previous["hashed_key"] != self.hashed_key
        )
        if changed:
            invalidate_auth_payload(previous["hashed_key"])
            invalidate_auth_payload(self.hashed_key)

    def delete(self, *args, **kwargs):
        invalidate_auth_payload(self.hashed_key)
        return super().delete(*args, **kwargs)
