from apps.accounts.views import UserViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"", UserViewSet, basename="user")


urlpatterns = [path("", include(router.urls))]
