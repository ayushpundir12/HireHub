from django.contrib import admin
from django.utils.timezone import now
from .models import ProApplication
from apps.pros.models import ProProfile


@admin.register(ProApplication)
class ProApplicationAdmin(admin.ModelAdmin):

    list_display  = ['user', 'full_name', 'service_category', 'status', 'is_fully_verified_display', 'submitted_at', 'reviewed_by']
    list_filter   = ['status', 'service_category', 'kyc_verified', 'pcc_verified', 'skills_verified', 'location_verified']
    search_fields = ['user__email', 'full_name', 'phone_number']
    readonly_fields = ['user', 'submitted_at', 'created_at', 'updated_at', 'reviewed_by', 'reviewed_at']
    actions = ['approve_applications', 'reject_applications', 'mark_under_review', 'request_resubmission']

    fieldsets = (
        ('Status', {
            'fields': ('status',)
        }),
        ('Personal Info', {
            'fields': ('user', 'full_name', 'date_of_birth', 'phone_number', 'bio')
        }),
        ('Service Info', {
            'fields': ('service_category', 'years_of_experience', 'portfolio_link')
        }),
        ('KYC Documents', {
            'fields': ('kyc_document_type', 'kyc_document_number', 'kyc_document_front', 'kyc_document_back', 'selfie_with_id', 'kyc_verified')
        }),
        ('Police Clearance Certificate', {
            'fields': ('pcc_document', 'pcc_issue_date', 'pcc_issuing_authority', 'pcc_verified')
        }),
        ('Skill Certificates', {
            'fields': ('skill_certificate_1', 'skill_certificate_2', 'skill_certificate_3', 'skills_verified')
        }),
        ('Location Proof', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'pincode', 'location_document_type', 'location_document', 'location_verified')
        }),
        ('Admin Review', {
            'fields': ('admin_notes', 'rejection_reason', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Fully Verified', boolean=True)
    def is_fully_verified_display(self, obj):
        return obj.is_fully_verified

    @admin.action(description='✅ Approve selected applications')
    def approve_applications(self, request, queryset):
        approved_count = 0
        for application in queryset:
            if application.status == ProApplication.Status.APPROVED:
                continue
            application.status      = ProApplication.Status.APPROVED
            application.reviewed_by = request.user
            application.reviewed_at = now()
            application.save()

            user = application.user
            user.role = 'pro'
            user.save(update_fields=['role'])

            ProProfile.objects.update_or_create(
                user=user,
                defaults={
                    'category':   application.service_category,
                    'experience': application.years_of_experience,
                    'bio':        application.bio,
                    'city':       application.city,
                    'state':      application.state,
                }
            )
            approved_count += 1
        self.message_user(request, f'{approved_count} application(s) approved and Pro profiles created.')

    @admin.action(description='❌ Reject selected applications')
    def reject_applications(self, request, queryset):
        queryset.exclude(status=ProApplication.Status.APPROVED).update(
            status=ProApplication.Status.REJECTED
        )
        self.message_user(request, f'{queryset.count()} application(s) rejected.')

    @admin.action(description='🔍 Mark as Under Review')
    def mark_under_review(self, request, queryset):
        queryset.filter(status=ProApplication.Status.SUBMITTED).update(
            status=ProApplication.Status.UNDER_REVIEW
        )
        self.message_user(request, f'{queryset.count()} application(s) marked as under review.')

    @admin.action(description='🔄 Request Resubmission')
    def request_resubmission(self, request, queryset):
        queryset.exclude(status=ProApplication.Status.APPROVED).update(
            status=ProApplication.Status.RESUBMISSION_REQUIRED
        )
        self.message_user(request, f'{queryset.count()} application(s) flagged for resubmission.')
    

    