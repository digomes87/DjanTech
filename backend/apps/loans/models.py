import uuid
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base: every important model gets created_at/updated_at"""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LoanApplication(TimeStampedModel):
    """Core entity: a customer application for home equity investiment"""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        FUNDED = "funded", "Funded"
        CLOSED = "closed", "Closed"

    VALID_TRANSITIONS = {
        Status.DRAFT: [Status.SUBMITTED],
        Status.SUBMITTED: [Status.APPROVED, Status.REJECTED],
        Status.UNDER_REVIEW: [Status.APPROVED, Status.REJECTED],
        Status.APPROVED: [Status.FUNDED, Status.REJECTED],
        Status.FUNDED: [Status.CLOSED],
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.CharField(max_length=20, unique=True, db_index=True)
    applicant = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="load_applications",
    )

    property = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="loan_applications",
    )

    analyst = models.ForeignKey(
        "properties.Property",
        on_delete=models.PROTECT,
        related_name="load_applications",
    )
    request_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("10000.00"))],
    )

    approved_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    investiment_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("1")), MaxValueValidator(Decimal("50"))],
        help_text="Percentage of home equity acquired by investor",
    )

    term_months = models.PositiveIntegerField(
        validators=[MinValueValidator(12), MaxValueValidator(360)],
    )

    credit_score = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    ltv_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    rejecyion_reason = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    funded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "loans_applications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["applicant", "status"]),
        ]

    def __str__(self) -> str:
        return f"LoanApplication({self.reference_number}. {self.status})"

    def can_transition_to(self, new_status: str) -> bool:
        allowed = self.VALID_TRANSITIONS.get(self.status, [])
        return new_status in allowed

    @property
    def is_active(self) -> bool:
        return self.status not in [self.Status.REJECTED, self.Status.CLOSED]

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = self._generate_reference()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_reference() -> str:
        import random
        import string

        suffix = "".join(random.choices(string.digits, k=8))
        return f"HEI-{suffix}"


class LoanDocuments(TimeStampedModel):
    """Documents attached to a loan application"""

    class DocumentType(models.TextChoices):
        ID_PROOF = "id_proof", "Identity Proof"
        INCOME = "income", "Income Proof"
        PROPERTY_DEED = "property_deed", "Property Deed"
        APPRAISAL = "appraisal", "Property Appraisal"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_application = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="uploaded_documents",
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(upload_to="loan_documents/%Y/%m/")
    original_filename = models.PositiveIntegerField(help_text="Size in bytes")
    is_verified = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_documents",
    )

    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "loans_documents"
        ordering = ["-created_at"]
