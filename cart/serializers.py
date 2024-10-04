from rest_framework import serializers
from .models import ShippingInfo


class ShippingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingInfo
        fields = ['id', 'comment', 'latitude', 'longitude']

    def validate_latitude(self, value):
        if not (-90 <= value <= 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if not (-180 <= value <= 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value


class PaymentSerializer(serializers.Serializer):
    amount = serializers.IntegerField(help_text="To'lov miqdori (centlarda)")
    currency = serializers.CharField(max_length=3, default='usd', help_text="Valyuta kodi")
    token = serializers.CharField(help_text="Stripe to'lov tokeni")

