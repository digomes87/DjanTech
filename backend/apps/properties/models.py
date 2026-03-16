import uuid
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Property(models.Model):
    """Real estate property owned by a user"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="properties"
    )
    address_street = models.CharField(max_length=255)
    address_city = models.CharField(max_length=100)
    address_state = models.CharField(max_length=2)
    address_zip = models.CharField(max_length=10)
    estimated_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("1000.00"))],
    )
    bedrooms = models.PositiveSmallIntegerField()
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1)
    square_feet = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "properties"
        ordering = ["-created_at"]
        verbose_name_plural = "Properties"

    def __str__(self) -> str:
        return self.full_address

    @property
    def full_address(self) -> str:
        return f"{self.address_street}, {self.address_city}, {self.address_state}, {self.address_zip}"

    @property
    def has_active_loan(self) -> bool:
        """Checl if property jas any non terminal loan application"""
        return self.loan_applications.filter(
            status__in=["draft", "submitted", "under_review", "approved"]
        ).exists()
