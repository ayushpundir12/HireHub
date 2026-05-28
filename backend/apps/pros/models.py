from django.db import models
from apps.users.models import User
import uuid


CATEGORY_CHOICES = [
    ('plumber',     'Plumber'),
    ('electrician', 'Electrician'),
    ('chef',        'Chef'),
    ('labour',      'General Labour'),
    ('carpenter',   'Carpenter'),
    ('painter',     'Painter'),
    ('cleaner',     'Cleaner'),
    ('mechanic',    'Mechanic'),
    ('gardener',    'Gardener'),
    ('mason',       'Mason'),
]


class ProProfile(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pro_profile')
    category        = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    experience      = models.DecimalField(default=0, decimal_places=1, max_digits=3)
    bio             = models.TextField(blank=True)
    hourly_rate     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cover_photo_url = models.TextField(blank=True)
    avg_rating      = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_jobs      = models.IntegerField(default=0)
    is_available    = models.BooleanField(default=True)
    city            = models.CharField(max_length=100, blank=True)
    state           = models.CharField(max_length=100, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pro_profiles'

    def __str__(self):
        return f"{self.user.full_name} — {self.category}"