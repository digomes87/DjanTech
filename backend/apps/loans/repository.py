"""
Centralizes all database access for LoanApplication
Ther service layer never call. objects.filter() directly

benefits:
    queries are on one place
    service logis is clean and readable
    easy to mock in tests without touchind in DB
"""

from typing import Optional

from apps.accounts.models import User
from apps.loans.models import LoanApplication
from django.db import models


class LoanRepository:
    @staticmethod
    def get_for_user(user: User, status: Optional[str] = None) -> models.QuerySet:
        """
        Returns applicatio visible to the user
        Analysts see all, applicants only see theris own
        Optimized with select_related + prefetch_related
        """
        qs = LoanApplication.objects.select_related(
            "applicant", "property", "analyst"
        ).prefetch_related("documents")

        if not (user.is_analyst or user.is_admin_user):
            qs = qs.filter(applicant=user)

        if status:
            qs = qs.filter(status=status)

        return qs

    @staticmethod
    def get_by_id(application_id: str) -> LoanApplication:
        return (
            LoanApplication.objects.select_related("applicant", "property", "analyst")
            .prefetch_related("documents")
            .get(id=application_id)
        )

    @staticmethod
    def get_prendind_review() -> models.QuerySet:
        """All applications awaiting analyst reviews"""
        return (
            LoanApplication.objects.filter(status=LoanApplication.Status.UNDER_REVIEW)
            .select_related("applicant", "property")
            .order_by("submitted_at")
        )

    @staticmethod
    def get_dashboard_stats(user: User) -> dict:
        """
        Aggregate stats for user dashboard.
        runs as a single query using aggregate + condicional count
        """

        from django.db.models import Count, Q, Sum

        qs = LoanApplication.objects.filter(applicant=user)

        return qs.aggregate(
            total=Count("id"),
            total_requested=Sum("requested_amount"),
            total_approved=Sum("approved_amount"),
            draft_count=Count("id", filter=Q(status="submitted")),
            submitted_count=Count("id", filter=Q(status="submitted")),
            under_review_count=Count("id", filter=Q(status="under_review")),
            approved_count=Count("id", filter=Q(status="approved")),
            rejected_count=Count("id", filter=Q(status="rejected")),
            funded_count=Count("id", filter=Q(status="funded")),
        )
