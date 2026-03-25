from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerSplitView,
)

API_V1 = "api/v1/"


urlpatterns = [
    path("admin/", admin.site.urls),
    path(API_V1 + "auth/", include("apps.accounts.urls.auth")),
    path(API_V1 + "users/", include("apps.loans.urls")),
    path(API_V1 + "properties/", include("apps.properties.urls")),
    path(API_V1 + "notifications/", include("apps.notifications.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
]
