from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tests.views_machine_relaxed import MachineUsersRelaxedViewSet

router = DefaultRouter()
router.register("machine-users-relaxed", MachineUsersRelaxedViewSet, basename="machine-users-relaxed")

urlpatterns = [
    path("", include(router.urls)),
]
