from rest_framework import serializers
from apps.users.models import User
from .models import ProProfile, CATEGORY_CHOICES


class ProProfileUpdateSerializer(serializers.ModelSerializer):
    """For PATCH /pro/profile/ — pro updates their own profile."""

    class Meta:
        model = ProProfile
        fields = [
            'category', 'bio', 'hourly_rate', 'cover_photo_url',
            'is_available', 'city', 'state', 'experience',
        ]
        extra_kwargs = {field: {'required': False} for field in fields}


class ProPublicSerializer(serializers.ModelSerializer):
    """Public-facing pro card — used in discovery list and public profile."""

    user_id      = serializers.UUIDField(source='user.id', read_only=True)
    full_name    = serializers.CharField(source='user.full_name', read_only=True)
    avatar_url   = serializers.CharField(source='user.avatar_url', read_only=True)
    locality     = serializers.CharField(source='user.locality', read_only=True)
    category_label = serializers.CharField(
        source='get_category_display', read_only=True
    )

    class Meta:
        model = ProProfile
        fields = [
            'id', 'user_id', 'full_name', 'avatar_url', 'locality',
            'category', 'category_label', 'experience', 'bio',
            'hourly_rate', 'cover_photo_url', 'avg_rating',
            'total_jobs', 'is_available', 'city', 'state',
        ]


class ProOwnProfileSerializer(serializers.ModelSerializer):
    """Full profile returned to the pro themselves — PATCH /pro/profile/."""

    user_id    = serializers.UUIDField(source='user.id', read_only=True)
    full_name  = serializers.CharField(source='user.full_name', read_only=True)
    email      = serializers.EmailField(source='user.email', read_only=True)
    avatar_url = serializers.CharField(source='user.avatar_url', read_only=True)
    category_label = serializers.CharField(
        source='get_category_display', read_only=True
    )

    class Meta:
        model = ProProfile
        fields = [
            'id', 'user_id', 'full_name', 'email', 'avatar_url',
            'category', 'category_label', 'experience', 'bio',
            'hourly_rate', 'cover_photo_url', 'avg_rating',
            'total_jobs', 'is_available', 'city', 'state',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['avg_rating', 'total_jobs', 'created_at', 'updated_at']