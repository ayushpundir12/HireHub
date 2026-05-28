from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for reading/updating user profiles."""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role',
            'locality',
            'phone_number', 'lat', 'lng',
            'avatar_url', 'created_at', 'updated_at',
            'is_email_verified', 'is_number_verified',
        ]

        # Security: fields the user should NEVER be able to edit via API
        read_only_fields = [
            'id', 'email', 'created_at', 'updated_at',
            'role', 'is_email_verified', 'is_number_verified',
        ]


class SignupSerializer(serializers.Serializer):
    """Validates signup data before creating a Supabase Auth user + Django profile."""

    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(max_length=100)
    phone_number=serializers.CharField(max_length=15)


class VerifySerializer(serializers.Serializer):
    email_otp = serializers.CharField(min_length=6, max_length=6)
    phone_otp = serializers.CharField(min_length=6, max_length=6)

    