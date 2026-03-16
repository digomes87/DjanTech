import logging
from decimal import Decimal

from apps.loans.models import LoanApplication
from core.exceptions import (
    BusinessRuleViolation,
    InsufficientPermissions,
)
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from backend.core.exceptions.handlers import InvalidStatusTransition

User = get_user_model()
logger = logging.getLogger(__name__)


class LoanApplicationService:
    """
    All loan bussines logic is here
    """

    MAX_LTV_RATIO = Decimal("0.80")

    @classmethod
    @transaction.atomic
    def create_application(
        cls,
        applicant: User,
        property_id: str,
        requested_amount: Decimal,
        term_months: int,
    ) -> LoanApplication:
        """
        Create a new draft loan application
        @transaction.atomic if anything fails everthing roll back
        """
        from apps.properties.models import Property

        try:
            property_ = Property.objects.select_for_update().get(id=property_id)
        except Property.DoesNotExist:
            raise BusinessRuleViolation("Property not found")

        if property_.owner != applicant:
            raise InsufficientPermissions(
                "You can only apply for loans on properties you own"
            )

        if property_.has_active_loan:
            raise BusinessRuleViolation(
                "This property already has an active loan application"
            )

        max_amount = property_.estimated_value * cls.MAX_LTV_RATIO
        if requested_amount > max_amount:
            raise BusinessRuleViolation(
                f"Requested amount exceeds 80% LTV limit. Maximo: ${max_amount}"
            )

        application = LoanApplication.objects.create(
            applicant=applicant,
            property=property_,
            requested_amount=requested_amount,
            term_months=term_months,
        )

        logger.info(
            "LoanApplication created",
            extra={
                "application_id": str(application.id),
                "applicant_id": str(applicant.id),
            },
        )
        return application

    @classmethod
    @transaction.atomic
    def submit_application(
        cls, application: LoanApplication, submitted_by: User
    ) -> LoanApplication:
        """
        Submit application for review. Trigger async credit check
        """

        from apps.loans.tasks import (
            run_credit_check_task,
        )

        if application.applicant != submitted_by:
            raise InsufficientPermissions(
                "Only the applicant can submit this application"
            )

        if not application.can_transition_to(LoanApplication.Status.SUBMITTED):
            raise InvalidStatusTransition(
                f"Cannot submit application in status {application.status}"
            )

        cls._assert_required_documents(application)

        application.status = LoanApplication.Status.SUBMITTED
        application.submitted_at = timezone.now()
        application.save(update_fields=["status", "submitted_at", "updated_at"])

        # fire async tasks
        run_credit_check_task.apply_async(
            args=[str(application.id)],
            queue="high_priority",
        )
