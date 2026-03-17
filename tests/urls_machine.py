from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tests.views_machine import MachineUsersViewSet

router = DefaultRouter()
router.register("machine-users", MachineUsersViewSet, basename="machine-users")

urlpatterns = [
    path("", include(router.urls)),
]
