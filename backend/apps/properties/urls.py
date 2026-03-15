from apps.properties.views import PropertyViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"", PropertyViewSet, basename="property")

urlpatterns = [path("", include(router.urls))]
