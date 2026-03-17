from django.urls import include, path
from rest_framework.routers import DefaultRouter

from django_machine_auth.views import MachineAPIKeyManagementViewSet

router = DefaultRouter()
router.register("machine-api-keys", MachineAPIKeyManagementViewSet, basename="machine-api-keys")

urlpatterns = [
    path("", include(router.urls)),
]
