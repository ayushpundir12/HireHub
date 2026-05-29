import uuid
from django.db import models
from apps.users.models import User


class Booking(models.Model):

    STATUS_PENDING     = 'pending'
    STATUS_CONFIRMED   = 'confirmed'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED   = 'completed'
    STATUS_CANCELLED   = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING,     'Pending'),
        (STATUS_CONFIRMED,   'Confirmed'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED,   'Completed'),
        (STATUS_CANCELLED,   'Cancelled'),
    ]

    # Valid transitions: who can move booking to which state
    # Format: {current_status: [allowed_next_statuses]}
    PRO_TRANSITIONS = {
        STATUS_PENDING:     [STATUS_CONFIRMED, STATUS_CANCELLED],
        STATUS_CONFIRMED:   [STATUS_IN_PROGRESS, STATUS_CANCELLED],
        STATUS_IN_PROGRESS: [STATUS_COMPLETED],
    }

    PAYMENT_CASH    = 'cash'
    PAYMENT_PREPAID = 'prepaid'

    PAYMENT_MODE_CHOICES = [
        (PAYMENT_CASH,    'Cash on Delivery'),
        (PAYMENT_PREPAID, 'Prepaid'),
    ]

    PAYMENT_UNPAID   = 'unpaid'
    PAYMENT_PAID     = 'paid'
    PAYMENT_REFUNDED = 'refunded'

    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID,   'Unpaid'),
        (PAYMENT_PAID,     'Paid'),
        (PAYMENT_REFUNDED, 'Refunded'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_as_client')
    pro            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_as_pro')
    category       = models.CharField(max_length=50)
    description    = models.TextField(blank=True)
    scheduled_at   = models.DateTimeField()
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_mode   = models.CharField(max_length=10, choices=PAYMENT_MODE_CHOICES)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_UNPAID)
    stripe_pi_id   = models.CharField(max_length=100, blank=True)
    locality       = models.CharField(max_length=100, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
            models.Index(fields=['pro', 'status', 'scheduled_at']),
        ]

    def __str__(self):
        return f"Booking {self.id} — {self.client} → {self.pro} [{self.status}]"

    def can_transition_to(self, new_status: str) -> bool:
        """
        Check if the pro is allowed to move to new_status from current status.
        This is the state machine guard — called in the view before saving.
        """
        allowed = self.PRO_TRANSITIONS.get(self.status, [])
        return new_status in allowed


class Review(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking    = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    client     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    pro        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating     = models.PositiveSmallIntegerField()  # 1–5, validated in serializer
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.client} for {self.pro} — {self.rating}★"