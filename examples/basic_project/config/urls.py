from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from demoapp.views import DemoUserViewSet

router = DefaultRouter()
router.register("demo-users", DemoUserViewSet, basename="demo-users")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(router.urls)),
]
