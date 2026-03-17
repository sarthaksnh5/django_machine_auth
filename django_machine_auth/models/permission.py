from django.db import models


class MachinePermission(models.Model):
    module = models.CharField(max_length=100, db_index=True)
    permission = models.CharField(max_length=255, db_index=True)
    label = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("module", "permission")
        ordering = ["module", "permission"]
