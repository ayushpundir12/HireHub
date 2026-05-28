from django.db import models
import uuid


class User(models.Model):
    """
    HireHub user profile — synced with Supabase Auth.
    The `id` matches the Supabase Auth user UUID (`auth.users.id`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    role = models.CharField(
        max_length=10,
        choices=[
            ('client', 'Client'),
            ('pro', 'Pro'),
            ('admin', 'Admin')
        ],
        default='client'  # everyone starts as client
    )
    locality = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True,unique=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    avatar_url = models.TextField(blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_number_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auth_provider = models.CharField(
                        max_length=20,
                        choices=[
                            ('email','Email'),
                            ('google','Google'),
                            ('facebook','Facebook'),
                        ],
                        default='email'
                    )

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def is_authenticated(self):
        """Required by DRF since we're not using AbstractBaseUser."""
        return True
