from django.urls import include, path
from rest_framework.routers import DefaultRouter

from django_machine_auth.views import (
    MachineAPIKeyManagementViewSet,
    MachineAPIKeyRequestLogViewSet,
    MachinePermissionViewSet,
)

router = DefaultRouter()
router.register("permissions", MachinePermissionViewSet, basename="machine-permissions")
router.register("machine-api-keys", MachineAPIKeyManagementViewSet, basename="machine-api-keys")
router.register("request-logs", MachineAPIKeyRequestLogViewSet, basename="machine-request-logs")

urlpatterns = [
    path("", include(router.urls)),
]
