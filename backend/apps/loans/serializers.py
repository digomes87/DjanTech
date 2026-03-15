"""
Serializers
"""

"""DRF Serializers for Loan Application."""
from decimal import Decimal

from apps.accounts.serializers import UserSummarySerializer
from apps.loans.models import LoanApplication, LoanDocument
from django.utils import timezone
from rest_framework import serializers


class LoanDocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSummarySerializer(read_only=True)

    class Meta:
        model = LoanDocument
        fields = [
            "id",
            "document_type",
            "original_filename",
            "file_size",
            "is_verified",
            "uploaded_by",
            "created_at",
        ]
        read_only_fields = ["id", "is_verified", "uploaded_by", "created_at"]


class LoanApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list endpoints — avoids over-fetching."""

    applicant_name = serializers.CharField(source="applicant.full_name", read_only=True)
    property_address = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "reference_number",
            "status",
            "requested_amount",
            "applicant_name",
            "property_address",
            "created_at",
        ]

    def get_property_address(self, obj) -> str:
        return getattr(obj.property, "full_address", "")


class LoanApplicationDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for retrieve endpoints."""

    applicant = UserSummarySerializer(read_only=True)
    analyst = UserSummarySerializer(read_only=True)
    documents = LoanDocumentSerializer(many=True, read_only=True)
    days_since_submission = serializers.SerializerMethodField()
    can_be_cancelled = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "reference_number",
            "status",
            "applicant",
            "analyst",
            "requested_amount",
            "approved_amount",
            "investment_percentage",
            "term_months",
            "credit_score",
            "ltv_ratio",
            "rejection_reason",
            "submitted_at",
            "approved_at",
            "funded_at",
            "created_at",
            "updated_at",
            "documents",
            "days_since_submission",
            "can_be_cancelled",
        ]
        read_only_fields = fields

    def get_days_since_submission(self, obj) -> int | None:
        if not obj.submitted_at:
            return None
        return (timezone.now() - obj.submitted_at).days

    def get_can_be_cancelled(self, obj) -> bool:
        request = self.context.get("request")
        if not request:
            return False
        return obj.applicant == request.user and obj.status == "draft"


class LoanApplicationCreateSerializer(serializers.Serializer):
    """Write serializer for creating an application."""

    property_id = serializers.UUIDField()
    requested_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    term_months = serializers.IntegerField(min_value=12, max_value=360)

    def validate_requested_amount(self, value: Decimal) -> Decimal:
        if value < Decimal("10000"):
            raise serializers.ValidationError("Minimum loan amount is $10,000.")
        return value


class LoanApplicationApproveSerializer(serializers.Serializer):
    approved_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    investment_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_investment_percentage(self, value: Decimal) -> Decimal:
        if not (Decimal("1") <= value <= Decimal("50")):
            raise serializers.ValidationError(
                "Investment percentage must be between 1% and 50%."
            )
        return value


class LoanApplicationRejectSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=10)
