from apps.properties.models import Property
from rest_framework import serializers


class PropertySummarySerializer(serializers.ModelSerializer):
    full_address = serializers.CharField(read_only=True)
    has_active_loan = serializers.BooleanField(read_only=True)

    class Meta:
        model = Property
        fields = ["id", "full_address", "estimated_value", "has_active_loan"]


class PropertySerializer(serializers.ModelSerializer):
    model = Property
    fields = [
        "id",
        "address_street",
        "address_city",
        "address_state",
        "address_zip",
        "full_address",
        "estimated_value",
        "bedrooms",
        "bathrooms",
        "square_feet",
        "has_active_loan",
        "created_at",
    ]
    read_only_fields = [
        "id",
        "has_active_loan",
        "created_at",
    ]
