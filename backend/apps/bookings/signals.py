from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import Review


@receiver(post_save, sender=Review)
def update_pro_rating(sender, instance, created, **kwargs):
    """
    Fires automatically after every Review INSERT.
    Recalculates avg_rating and total_jobs on ProProfile.
    
    Why a signal instead of doing this in the view?
    Because rating updates are a CONSEQUENCE of a review existing,
    not a responsibility of the view that created the review.
    The view's job is to save the review. The signal handles the aftermath.
    """
    if not created:
        return  # only fire on new reviews, not edits

    from apps.pros.models import ProProfile
    from apps.pros.cache import invalidate_pro_cache

    stats = Review.objects.filter(pro=instance.pro).aggregate(
        avg=Avg('rating'),
        total=Count('id')
    )

    ProProfile.objects.filter(user=instance.pro).update(
        avg_rating=stats['avg'] or 0,
        total_jobs=stats['total'],
    )

    # Bust the pro's cache so discovery shows fresh rating
    try:
        profile = ProProfile.objects.get(user=instance.pro)
        invalidate_pro_cache(profile.id)
    except ProProfile.DoesNotExist:
        pass