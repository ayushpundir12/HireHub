from rest_framework import serializers
from .models import ProApplication

class PersonalInfoSerializers(serializers.ModelSerializers):
    class Meta:
        model=[ProApplication]
        fields=['full_name','date_of_birth','phone_number','bio']

class ServiceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=[ProApplication]
        fields=['service_category','years_of_experience','portfolio_link ']

class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model=[ProApplication]
        fields=['kyc_document_type',
                'kyc_document_number',
                'kyc_document_front',
                'kyc_document_back',
                'selfie_with_id'
                ]


class PCCSerializer(serializers.ModelSerializer):
    class Meta:
        model=[ProApplication]
        fields=['pcc_document', 'pcc_issue_date', 'pcc_issuing_authority']

class SkillCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model=[ProApplication]
        fields=['skill_certificate_1','skill_certificate_2','skill_certificate_3']

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
    class Meta:
        model=[ProApplication]
        fields = [
            'id', 'user_id', 'full_name', 'email', 'avatar_url',
            'category', 'category_label', 'experience', 'bio',
            'hourly_rate', 'cover_photo_url', 'avg_rating',
            'total_jobs', 'is_available', 'city', 'state',
            'created_at', 'updated_at',
        ]
        
