from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.bookings.models import Booking, Review


@receiver(post_save, sender=Booking)
def booking_status_changed(sender, instance, created, **kwargs):
    """
    Fires on every Booking save.
    Routes to the right Celery task based on new status.

    Why check `created` separately?
    On creation, status is always 'pending' → notify pro of new booking.
    On update, we check which status it changed to.

    Why .delay()?
    Queues the task in Redis and returns immediately.
    The view doesn't wait for the notification to be created.
    """
    from .tasks import (
        notify_booking_received,
        notify_booking_confirmed,
        notify_booking_cancelled,
        notify_booking_completed,
    )

    if created:
        # New booking — notify pro
        notify_booking_received.delay(str(instance.id))
        return

    # Status update — check what it changed to
    if instance.status == Booking.STATUS_CONFIRMED:
        notify_booking_confirmed.delay(str(instance.id))

    elif instance.status == Booking.STATUS_CANCELLED:
        notify_booking_cancelled.delay(str(instance.id))

    elif instance.status == Booking.STATUS_COMPLETED:
        notify_booking_completed.delay(str(instance.id))


@receiver(post_save, sender=Review)
def review_created(sender, instance, created, **kwargs):
    """Fires when a new review is saved."""
    if not created:
        return

    from .tasks import notify_review_received
    notify_review_received.delay(str(instance.id))