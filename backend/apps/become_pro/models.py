from django.db import models
import uuid
from apps.users.models import User
from .validators import validate_file_size
from apps.pros.models import CATEGORY_CHOICES

class ProApplication(models.Model):

    def application_document_upload_path(instance, filename):
        return f"pro_applications/{instance.user.id}/{filename}"


    class Status(models.TextChoices):
        DRAFT                 = 'draft',                 'Draft'
        SUBMITTED             = 'submitted',             'Submitted'
        UNDER_REVIEW          = 'under_review',          'Under Review'
        APPROVED              = 'approved',              'Approved'
        REJECTED              = 'rejected',              'Rejected'
        RESUBMISSION_REQUIRED = 'resubmission_required', 'Resubmission Required'


    class KYCDocumentType(models.TextChoices):
        AADHAR          = 'aadhar',          'Aadhar Card'
        PAN             = 'pan',             'PAN Card'
        PASSPORT        = 'passport',        'Passport'
        VOTER_ID        = 'voter_id',        'Voter ID'
        DRIVING_LICENSE = 'driving_license', 'Driving License'
    
    class LocationDocumentType(models.TextChoices):
        UTILITY_BILL   = 'utility_bill',   'Utility Bill'
        BANK_STATEMENT = 'bank_statement', 'Bank Statement'
        RENT_AGREEMENT = 'rent_agreement', 'Rent Agreement'
        AADHAR         = 'aadhar',         'Aadhar Card (with address)'
        PASSPORT       = 'passport',       'Passport (with address)'

    #core
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="pro_application")
    status=models.CharField(max_length=30,choices=Status.choices,default=Status.DRAFT)

    #personal info
    full_name=models.CharField(max_length=100,blank=True)
    date_of_birth=models.DateField(null=True,blank=True)
    phone_number=models.CharField(max_length=15,blank=True)
    bio=models.TextField(blank=True)

    #service info
    service_category=models.CharField(max_length=50,choices=CATEGORY_CHOICES, blank=True)
    years_of_experience = models.PositiveSmallIntegerField(default=0)
    portfolio_link      = models.URLField(blank=True)


    #kyc
    kyc_document_type=models.CharField(max_length=20,choices=KYCDocumentType.choices,blank=True)
    kyc_document_number =models.CharField(max_length=50, blank=True)
    kyc_document_front=models.ImageField(upload_to=application_document_upload_path,validators=[validate_file_size],blank=True,null=True)
    kyc_document_back = models.ImageField(upload_to=application_document_upload_path,validators=[validate_file_size], blank=True, null=True)
    selfie_with_id  = models.ImageField(upload_to=application_document_upload_path,validators=[validate_file_size], blank=True, null=True)
    kyc_verified=models.BooleanField(default=False)

    #pcc
    pcc_document=models.ImageField(upload_to=application_document_upload_path,validators=[validate_file_size], blank=True, null=True)
    pcc_issue_date=models.DateField(blank=True,null=True)
    pcc_issuing_authority = models.CharField(max_length=150, blank=True)
    pcc_verified          = models.BooleanField(default=False)

    #skill certificate
    skill_certificate_1 = models.ImageField(upload_to=application_document_upload_path,validators=[validate_file_size], blank=True, null=True)
    skill_certificate_2 = models.ImageField(upload_to=application_document_upload_path,validators=[validate_file_size], blank=True, null=True)
    skill_certificate_3 = models.ImageField(upload_to=application_document_upload_path,validators=[validate_file_size], blank=True, null=True)
    skills_verified     = models.BooleanField(default=False)

    #address line
    address_line1= models.CharField(max_length=255,blank=True)
    address_line2= models.CharField(max_length=255,blank=True)
    city                   = models.CharField(max_length=100, blank=True)
    state                  = models.CharField(max_length=100, blank=True)
    pincode                = models.CharField(max_length=10, blank=True)
    location_document_type = models.CharField(max_length=20, choices=LocationDocumentType.choices, blank=True)
    location_document      = models.ImageField(upload_to=application_document_upload_path,validators=[validate_file_size], blank=True, null=True)
    location_verified      = models.BooleanField(default=False)


    #admin notes
    admin_notes      = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    reviewed_by      = models.ForeignKey(
                           User,
                           on_delete=models.SET_NULL,
                           null=True, blank=True,
                           related_name='reviewed_applications'
                       )
    reviewed_at = models.DateTimeField(null=True, blank=True)


    #timestamp
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table='pro_applications'
        ordering=['-created_at']
        verbose_name='Pro Application'
        verbose_name_plural='Pro Applications'

    
    def __str__(self):
        return f"{self.user.full_name} — {self.status}"

    @property
    def is_fully_verified(self):
        return all([
            self.kyc_verified,
            self.pcc_verified,
            self.skills_verified,
            self.location_verified
        ])




