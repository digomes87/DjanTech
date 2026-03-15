import logging

from apps.loans.repository import LoanRepository
from apps.loans.serializers import (
    LoanApplicationApproveSerializer,
    LoanApplicationCreateSerializer,
    LoanApplicationDetailSerializer,
    LoanApplicationListSerializer,
    LoanApplicationRejectSerializer,
)
from apps.loans.services import LoanApplicationService
from core.exceptions import (
    BusinessRuleViolation,
    InsufficientPermissions,
    InvalidStatusTransition,
)
from core.permissions import IsAnalystOrAdmin
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

logger = logging.getLogger(__name__)


class LoanApplicationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    viewset for loan application
    genericviewset + mixins granular control over which actions are available
    """

    def get_queryset(self):
        status_filter = self.request.query_params.get("status")
        return LoanRepository.get_for_user(
            user=self.request.user,
            status=status_filter,
        )
