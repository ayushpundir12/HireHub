from rest_framework import serializers
from apps.bookings.models import Booking


class InitiatePaymentSerializer(serializers.Serializer):
    booking_id = serializers.UUIDField()

    def validate_booking_id(self, value):
        try:
            booking = Booking.objects.get(id=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

        if booking.payment_mode != Booking.PAYMENT_PREPAID:
            raise serializers.ValidationError(
                "This booking uses cash on delivery. No payment needed."
            )

        if booking.payment_status == Booking.PAYMENT_PAID:
            raise serializers.ValidationError(
                "This booking is already paid."
            )

        return value


class VerifyPaymentSerializer(serializers.Serializer):
    """
    Frontend sends these three fields after Razorpay checkout completes.
    We use them to verify the payment signature.
    """
    razorpay_order_id   = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature  = serializers.CharField()