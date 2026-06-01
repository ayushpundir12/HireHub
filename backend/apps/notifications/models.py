import uuid
from django.db import models
from apps.users.models import User


class Notification(models.Model):

    # Notification types — add new ones here as the platform grows
    TYPE_BOOKING_RECEIVED   = 'booking_received'
    TYPE_BOOKING_CONFIRMED  = 'booking_confirmed'
    TYPE_BOOKING_CANCELLED  = 'booking_cancelled'
    TYPE_BOOKING_COMPLETED  = 'booking_completed'
    TYPE_KYC_APPROVED       = 'kyc_approved'
    TYPE_KYC_REJECTED       = 'kyc_rejected'
    TYPE_REVIEW_RECEIVED    = 'review_received'

    TYPE_CHOICES = [
        (TYPE_BOOKING_RECEIVED,  'Booking Received'),
        (TYPE_BOOKING_CONFIRMED, 'Booking Confirmed'),
        (TYPE_BOOKING_CANCELLED, 'Booking Cancelled'),
        (TYPE_BOOKING_COMPLETED, 'Booking Completed'),
        (TYPE_KYC_APPROVED,      'KYC Approved'),
        (TYPE_KYC_REJECTED,      'KYC Rejected'),
        (TYPE_REVIEW_RECEIVED,   'Review Received'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title      = models.CharField(max_length=100)
    message    = models.TextField()
    link       = models.CharField(max_length=200, blank=True)  # deep link e.g. /bookings/uuid
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"{self.type} → {self.user.full_name} ({'read' if self.is_read else 'unread'})"