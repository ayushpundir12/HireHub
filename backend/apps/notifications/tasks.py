from celery import shared_task
import logging

logger = logging.getLogger(__name__)


def _create_notification(user_id, type_, title, message, link=''):
    """
    Helper that actually writes to DB.
    Separated from the task so it can be called directly in tests.
    """
    from apps.users.models import User
    from .models import Notification

    try:
        user = User.objects.get(id=user_id)
        Notification.objects.create(
            user    = user,
            type    = type_,
            title   = title,
            message = message,
            link    = link,
        )
    except User.DoesNotExist:
        logger.error(f"Notification failed: user {user_id} not found.")
    except Exception as e:
        logger.error(f"Notification creation failed: {e}")


# ── Booking Notifications ─────────────────────────────────────────────────────

@shared_task
def notify_booking_received(booking_id: str):
    """Notify PRO when a client creates a booking."""
    from apps.bookings.models import Booking
    try:
        booking = Booking.objects.select_related('client', 'pro').get(id=booking_id)
    except Booking.DoesNotExist:
        return

    _create_notification(
        user_id = str(booking.pro.id),
        type_   = 'booking_received',
        title   = 'New Booking Request',
        message = f"{booking.client.full_name} has requested a booking for {booking.category} on {booking.scheduled_at.strftime('%b %d, %Y')}.",
        link    = f"/pro/bookings/{booking.id}",
    )


@shared_task
def notify_booking_confirmed(booking_id: str):
    """Notify CLIENT when pro confirms the booking."""
    from apps.bookings.models import Booking
    try:
        booking = Booking.objects.select_related('client', 'pro').get(id=booking_id)
    except Booking.DoesNotExist:
        return

    _create_notification(
        user_id = str(booking.client.id),
        type_   = 'booking_confirmed',
        title   = 'Booking Confirmed',
        message = f"{booking.pro.full_name} has confirmed your booking for {booking.scheduled_at.strftime('%b %d, %Y')}.",
        link    = f"/bookings/{booking.id}",
    )


@shared_task
def notify_booking_cancelled(booking_id: str):
    """Notify the OTHER party when a booking is cancelled."""
    from apps.bookings.models import Booking
    try:
        booking = Booking.objects.select_related('client', 'pro').get(id=booking_id)
    except Booking.DoesNotExist:
        return

    # Notify client
    _create_notification(
        user_id = str(booking.client.id),
        type_   = 'booking_cancelled',
        title   = 'Booking Cancelled',
        message = f"Your booking with {booking.pro.full_name} on {booking.scheduled_at.strftime('%b %d, %Y')} has been cancelled.",
        link    = f"/bookings/{booking.id}",
    )


@shared_task
def notify_booking_completed(booking_id: str):
    """Notify CLIENT when job is completed — prompt them to review."""
    from apps.bookings.models import Booking
    try:
        booking = Booking.objects.select_related('client', 'pro').get(id=booking_id)
    except Booking.DoesNotExist:
        return

    _create_notification(
        user_id = str(booking.client.id),
        type_   = 'booking_completed',
        title   = 'Job Completed!',
        message = f"Your job with {booking.pro.full_name} is complete. How did it go? Leave a review!",
        link    = f"/bookings/{booking.id}",
    )


# ── KYC Notifications ─────────────────────────────────────────────────────────

@shared_task
def notify_kyc_approved(pro_id: str):
    """Notify PRO when their KYC is approved."""
    _create_notification(
        user_id = pro_id,
        type_   = 'kyc_approved',
        title   = 'Profile Verified!',
        message = 'Your identity has been verified. Your profile is now live and visible to clients.',
        link    = '/pro/dashboard',
    )


@shared_task
def notify_kyc_rejected(pro_id: str, reason: str = ''):
    """Notify PRO when their KYC is rejected."""
    message = 'Your KYC submission was rejected.'
    if reason:
        message += f" Reason: {reason}"
    message += " Please resubmit with correct documents."

    _create_notification(
        user_id = pro_id,
        type_   = 'kyc_rejected',
        title   = 'KYC Rejected',
        message = message,
        link    = '/pro/kyc',
    )


# ── Review Notifications ──────────────────────────────────────────────────────

@shared_task
def notify_review_received(review_id: str):
    """Notify PRO when a client leaves a review."""
    from apps.bookings.models import Review
    try:
        review = Review.objects.select_related('client', 'pro').get(id=review_id)
    except Review.DoesNotExist:
        return

    stars   = '★' * review.rating + '☆' * (5 - review.rating)
    _create_notification(
        user_id = str(review.pro.id),
        type_   = 'review_received',
        title   = f'New Review {stars}',
        message = f"{review.client.full_name} left you a {review.rating}-star review.",
        link    = f"/pro/dashboard",
    )