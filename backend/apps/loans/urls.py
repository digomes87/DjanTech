from apps.loans.views import LoanApplicationViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"applications", LoanApplicationViewSet, basename="loanapplication")

urlpatterns = [path("", include(router.urls))]
