from django.urls import include, path

urlpatterns = [
    path("machine-auth/", include("django_machine_auth.urls")),
]
