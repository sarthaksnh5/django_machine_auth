from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MachineAPIKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("hashed_key", models.CharField(db_index=True, max_length=64, unique=True)),
                ("permissions", models.JSONField(default=list)),
                ("expires_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="machine_api_keys", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="MachinePermission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("module", models.CharField(db_index=True, max_length=100)),
                ("permission", models.CharField(db_index=True, max_length=255)),
                ("label", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["module", "permission"], "unique_together": {("module", "permission")}},
        ),
        migrations.CreateModel(
            name="APIKeyRequestLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("url", models.TextField()),
                ("method", models.CharField(max_length=10)),
                ("headers", models.JSONField(default=dict)),
                ("request_body", models.JSONField(blank=True, null=True)),
                ("response_body", models.JSONField(blank=True, null=True)),
                ("status_code", models.IntegerField()),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("duration", models.FloatField()),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("api_key", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="request_logs", to="django_machine_auth.machineapikey")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
