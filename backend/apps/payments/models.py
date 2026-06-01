import uuid
from django.db import models
from apps.users.models import User
from apps.bookings.models import Booking


class Payment(models.Model):

    STATUS_PENDING   = 'pending'
    STATUS_SUCCEEDED = 'succeeded'
    STATUS_FAILED    = 'failed'
    STATUS_REFUNDED  = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_SUCCEEDED, 'Succeeded'),
        (STATUS_FAILED,    'Failed'),
        (STATUS_REFUNDED,  'Refunded'),
    ]

    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking             = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    user                = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')

    # Razorpay specific fields
    razorpay_order_id   = models.CharField(max_length=100, unique=True)       # order_xxxxxxxx
    razorpay_payment_id = models.CharField(max_length=100, blank=True)        # pay_xxxxxxxx — filled after payment
    razorpay_signature  = models.CharField(max_length=200, blank=True)        # verification signature

    amount              = models.DecimalField(max_digits=10, decimal_places=2)
    currency            = models.CharField(max_length=10, default='INR')
    status              = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    razorpay_event_id   = models.CharField(max_length=100, blank=True)        # webhook idempotency
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.razorpay_order_id} — {self.amount} {self.currency} [{self.status}]"