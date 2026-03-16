import logging
from os import truncate

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
from rest_framework import status
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
            user=self.request.user,  # type: ignore[arg-type]
            status=status_filter,
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LoanApplicationDetailSerializer
        return LoanApplicationListSerializer

    @extend_schema(
        request=LoanApplicationCreateSerializer,
        responses={201: LoanApplicationDetailSerializer},
    )
    def create(self, request):
        serializer = LoanApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            application = LoanApplicationService.create_application(
                applicant=request.user, **serializer.validated_data
            )

        except (BusinessRuleViolation, InsufficientPermissions) as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        return Response(
            LoanApplicationDetailSerializer(
                application, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="submit")  # type: ignore[arg-type]
    def submit(self, request, pk: str | None = None):
        application = self.get_object()
        try:
            application = LoanApplicationService.submit_application(
                application=application,
                submitted_by=request.user,
            )
        except (
            BusinessRuleViolation,
            InvalidStatusTransition,
            InsufficientPermissions,
        ) as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

    @action(detail=True, methods=["post"], url_path="approve")  # type: ignore[arg-type]
    def approve(self, request, pk: str | None = None):
        application = self.get_object()
        serializer = LoanApplicationApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            application = LoanApplicationService.approve_application(
                application=application,
                analyst=request.user,
                **serializer.validated_data,
            )
        except (InvalidStatusTransition, InsufficientPermissions) as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        return Response(
            LoanApplicationDetailSerializer(
                application, context={"request": request}
            ).data
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
        permission_classes=[IsAnalystOrAdmin],
    )
    def reject(self, request, pk=None):
        application = self.get_object()
        serializer = LoanApplicationRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            application = LoanApplicationService.reject_application(
                application=application,
                rejected_by=request.user,
                reason=serializer.validated_data["reason"],
            )
        except (InvalidStatusTransition, InsufficientPermissions) as e:
            return Response(
                {"detail": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        return Response(
            LoanApplicationDetailSerializer(
                application, context={"request": request}
            ).data
        )

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        """Aggregate stats — single DB query using aggregate."""
        stats = LoanRepository.get_dashboard_stats(user=request.user)
        return Response(stats)
