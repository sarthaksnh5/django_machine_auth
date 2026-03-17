from django import forms
from django.contrib import admin, messages

from django_machine_auth.models import APIKeyRequestLog, MachineAPIKey, MachinePermission
from django_machine_auth.utils.cache import invalidate_auth_payload
from django_machine_auth.utils.hashing import hash_api_key
from django_machine_auth.utils.key_generator import generate_api_key


class MachineAPIKeyAdminForm(forms.ModelForm):
    permission_search = forms.CharField(
        required=False,
        label="Search permissions",
        help_text="Filter permissions by module/action text before selection.",
    )
    permissions = forms.MultipleChoiceField(required=False, widget=forms.SelectMultiple(attrs={"size": 18}))

    class Meta:
        model = MachineAPIKey
        fields = ["name", "user", "permissions", "expires_at", "is_active"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.fields["name"].help_text = "Human-readable label used for operational tracking."
        self.fields["expires_at"].help_text = "Optional expiration timestamp. Expired keys are rejected."
        self.fields["is_active"].help_text = "Disable immediately to revoke key access."
        search_text = ""
        if self.request and self.request.method == "POST":
            search_text = (self.request.POST.get("permission_search") or "").strip()
        elif self.request:
            search_text = (self.request.GET.get("permission_search") or "").strip()

        queryset = MachinePermission.objects.all().order_by("module", "permission")
        if search_text:
            queryset = queryset.filter(permission__icontains=search_text)
        self.initial["permission_search"] = search_text
        self.fields["permissions"].choices = self._grouped_choices(queryset)
        self.initial["permissions"] = self.instance.permissions or []

    @staticmethod
    def _grouped_choices(queryset):
        grouped = {}
        for item in queryset:
            grouped.setdefault(item.module, []).append((item.permission, item.permission))
        return [(module, perms) for module, perms in grouped.items()]

    def clean_permissions(self):
        selected = self.cleaned_data.get("permissions") or []
        valid = set(MachinePermission.objects.values_list("permission", flat=True))
        invalid = [perm for perm in selected if perm not in valid]
        if invalid:
            raise forms.ValidationError(f"Invalid permissions: {', '.join(sorted(invalid))}")
        return list(selected)


@admin.register(MachineAPIKey)
class MachineAPIKeyAdmin(admin.ModelAdmin):
    form = MachineAPIKeyAdminForm
    list_display = ("name", "user", "is_active", "expires_at", "last_used_at", "created_at")
    list_filter = ("is_active", "user", "created_at", "expires_at")
    search_fields = ("name", "user__username", "user__email")
    readonly_fields = ("hashed_key", "created_at", "updated_at", "last_used_at")
    fields = ("name", "user", "permissions", "permission_search", "expires_at", "is_active", "hashed_key", "last_used_at", "created_at", "updated_at")

    def get_form(self, request, obj=None, **kwargs):
        base_form = super().get_form(request, obj, **kwargs)

        class RequestAwareForm(base_form):
            def __init__(self, *args, **inner_kwargs):
                inner_kwargs["request"] = request
                super().__init__(*args, **inner_kwargs)

        return RequestAwareForm

    def save_model(self, request, obj, form, change):
        generated_key = None
        if not change:
            generated_key = generate_api_key()
            obj.hashed_key = hash_api_key(generated_key)
        obj.permissions = form.cleaned_data.get("permissions", [])
        super().save_model(request, obj, form, change)
        invalidate_auth_payload(obj.hashed_key)

        if generated_key:
            self.message_user(
                request,
                f"Machine API key generated (copy now): {generated_key}",
                level=messages.WARNING,
            )


@admin.register(MachinePermission)
class MachinePermissionAdmin(admin.ModelAdmin):
    list_display = ("module", "permission", "label", "created_at")
    list_filter = ("module",)
    search_fields = ("module", "permission", "label")
    readonly_fields = ("created_at",)


@admin.register(APIKeyRequestLog)
class APIKeyRequestLogAdmin(admin.ModelAdmin):
    list_display = ("api_key", "user", "method", "status_code", "duration", "created_at")
    list_filter = ("method", "status_code", "created_at")
    search_fields = ("url", "api_key__name", "user__username")
    readonly_fields = [f.name for f in APIKeyRequestLog._meta.fields]
