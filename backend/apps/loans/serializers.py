"""
Serializers
"""

from decimal import Decimal

from apps.accounts.serializers import UserSummarySerializer
from apps.loans.models import LoanApplication, LoanDocuments
from django.utils import timezone
from rest_framework import serializers


class LoadDocumentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSummarySerializer(read_only=True)

    class Meta:
        model = LoanDocuments
        fields = [
            "id",
            "document_type",
            "original_filename",
            "file_size",
            "is_verified",
            "uploaded_by",
            "created_at",
        ]


class LoanApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list endpoints"""

    applicant_name = serializers.CharField(
        source="applicant.full_name",
        read_only=True,
    )

    property_address = serializers.SerializerMethodField()

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "reference_number",
            "status",
            "requestd_amount",
            "applicant_name",
            "property_address",
            "created_at",
        ]

        def get_property_address(self, obj) -> str:
            return getattr(obj.property, "full_address", "")


class LoanApplicationDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for retrieve endpoints"""

    applicant = UserSummarySerializer(read_only=True)
    analyss = UserSummarySerializer(read_only=True)
    documents = LoadDocumentSerializer(many=True, read_only=True)
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
            "investiment_percentage",
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


class LoanApplicantionCreateSerializer(serializers.Serializer):
    """Write serializer for creating an application"""

    property_id = serializers.UUIDField()
    requested_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    term_months = serializers.IntegerField(min_value=12, max_value=360)

    def validate_requested_amount(self, value: Decimal) -> Decimal:
        if value < Decimal("10000"):
            raise serializers.ValidationError("Minimum loan amount if $10.000.")
        return value


class LoanApplicationApproveSerializer(serializers.Serializer): ...
