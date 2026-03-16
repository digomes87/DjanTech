import logging

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    queue="high_priority",
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=120,
    time_limit=180,
)
def run_credit_check_task(self, application_id: str) -> dict:
    """
    Fetch credit score from external credit rating service.
    Retries up to 3 times on network failure (60s between retries).

    IDEMPOTENCY: running twice just overwrites with the same data — safe.
    """
    from apps.loans.models import LoanApplication

    logger.info(f"Starting credit check for application {application_id}")

    try:
        application = LoanApplication.objects.select_related("applicant").get(
            id=application_id
        )
    except LoanApplication.DoesNotExist:
        logger.error(f"Application {application_id} not found — skipping")
        return {"error": "Application not found"}

    try:
        # Simulated external service call
        # In production: from apps.loans.integrations.credit_service import CreditServiceClient
        credit_data = {"score": 720, "ltv_ratio": "65.00"}  # placeholder
    except Exception as exc:
        logger.warning(f"Credit check failed for {application_id}, retrying: {exc}")
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error(f"Credit check permanently failed for {application_id}")
            return {"error": str(exc)}

    application.credit_score = credit_data["score"]
    application.ltv_ratio = credit_data.get("ltv_ratio")
    application.save(update_fields=["credit_score", "ltv_ratio", "updated_at"])

    logger.info(
        f"Credit check complete for {application_id}: score={credit_data['score']}"
    )

    if credit_data["score"] >= 750:
        _auto_advance_to_review.delay(application_id)

    return {"application_id": application_id, "score": credit_data["score"]}


@shared_task(bind=True, queue="default", max_retries=3, default_retry_delay=30)
def send_application_submitted_notification(self, application_id: str) -> None:
    """Notify applicant that their application was received."""
    from apps.loans.models import LoanApplication
    from django.conf import settings
    from django.core.mail import send_mail

    try:
        application = LoanApplication.objects.select_related("applicant").get(
            id=application_id
        )
    except LoanApplication.DoesNotExist:
        return

    try:
        send_mail(
            subject=f"Application {application.reference_number} received",
            message=(
                f"Hi {application.applicant.first_name},\n\n"
                f"We received your application {application.reference_number}. "
                f"We'll review it shortly.\n\nFintech Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL
            if hasattr(settings, "DEFAULT_FROM_EMAIL")
            else "noreply@fintech.com",
            recipient_list=[application.applicant.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, queue="high_priority", max_retries=3, default_retry_delay=30)
def _auto_advance_to_review(self, application_id: str) -> None:
    from apps.loans.models import LoanApplication

    try:
        application = LoanApplication.objects.get(id=application_id)
        if application.status == LoanApplication.Status.SUBMITTED:
            application.status = LoanApplication.Status.UNDER_REVIEW
            application.save(update_fields=["status", "updated_at"])
            logger.info(f"Auto-advanced application {application_id} to under_review")
    except LoanApplication.DoesNotExist:
        pass
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def cleanup_expired_draft_applications() -> int:
    """
    Scheduled task (Celery Beat): delete drafts older than 30 days.
    """
    from datetime import timedelta

    from apps.loans.models import LoanApplication
    from django.utils import timezone

    cutoff = timezone.now() - timedelta(days=30)
    count, _ = LoanApplication.objects.filter(
        status=LoanApplication.Status.DRAFT,
        created_at__lt=cutoff,
    ).delete()

    logger.info(f"Cleaned up {count} expired draft applications")
    return count
