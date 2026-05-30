from rest_framework import serializers
from .models import ProApplication


class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProApplication
        fields = ['full_name', 'date_of_birth', 'phone_number', 'bio']


class ServiceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProApplication
        fields = ['service_category', 'years_of_experience', 'portfolio_link']


class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProApplication
        fields = [
            'kyc_document_type',
            'kyc_document_number',
            'kyc_document_front',
            'kyc_document_back',
            'selfie_with_id',
        ]


class PCCSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProApplication
        fields = ['pcc_document', 'pcc_issue_date', 'pcc_issuing_authority']


class SkillCertificatesSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProApplication
        fields = ['skill_certificate_1', 'skill_certificate_2', 'skill_certificate_3', 'portfolio_link']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProApplication
        fields = [
            'address_line1',
            'address_line2',
            'city',
            'state',
            'pincode',
            'location_document_type',
            'location_document',
        ]


class ProApplicationStatusSerializer(serializers.ModelSerializer):
    is_fully_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model  = ProApplication
        fields = [
            'id', 'status',
            'kyc_verified', 'pcc_verified', 'skills_verified', 'location_verified',
            'is_fully_verified',
            'submitted_at', 'created_at',
            'rejection_reason',
        ]