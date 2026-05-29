from rest_framework import serializers
from .models import Booking, Review
from apps.users.models import User


class BookingCreateSerializer(serializers.ModelSerializer):
    """Used by client to POST /bookings/"""

    class Meta:
        model  = Booking
        fields = [
            'pro', 'category', 'description',
            'scheduled_at', 'duration_hours',
            'amount', 'payment_mode', 'locality',
        ]

    def validate_rating(self, value):
        # Not on this serializer but shows the pattern
        pass

    def validate_pro(self, pro_user):
        """
        Ensure the target user is actually a pro
        and their profile is available.
        """
        if pro_user.role != 'pro':
            raise serializers.ValidationError("Selected user is not a pro.")
        return pro_user

    def validate_scheduled_at(self, value):
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future.")
        return value


class BookingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    client_name = serializers.CharField(source='client.full_name', read_only=True)
    pro_name    = serializers.CharField(source='pro.full_name', read_only=True)
    pro_avatar  = serializers.CharField(source='pro.avatar_url', read_only=True)
    has_review  = serializers.SerializerMethodField()

    class Meta:
        model  = Booking
        fields = [
            'id', 'client_name', 'pro_name', 'pro_avatar',
            'category', 'scheduled_at', 'amount',
            'status', 'payment_mode', 'payment_status',
            'created_at', 'has_review',
        ]

    def get_has_review(self, obj):
        # hasattr check avoids an extra query — review is a reverse OneToOne
        return hasattr(obj, 'review')


class BookingStatusUpdateSerializer(serializers.Serializer):
    """
    Used by PATCH /bookings/:id/status/
    We use a plain Serializer (not ModelSerializer) because
    we're only accepting one field and applying custom logic.
    """
    status = serializers.ChoiceField(choices=Booking.STATUS_CHOICES)


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Used by client to POST /bookings/:id/review/"""

    class Meta:
        model  = Review
        fields = ['rating', 'comment']

    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """Public read — used on pro profile page."""

    client_name   = serializers.CharField(source='client.full_name', read_only=True)
    client_avatar = serializers.CharField(source='client.avatar_url', read_only=True)

    class Meta:
        model  = Review
        fields = ['id', 'client_name', 'client_avatar', 'rating', 'comment', 'created_at']