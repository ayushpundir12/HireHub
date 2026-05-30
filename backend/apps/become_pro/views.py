from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.timezone import now

from apps.users.permissions import IsFullyVerified
from .models import ProApplication
from .serializers import (
    PersonalInfoSerializer,
    ServiceInfoSerializer,
    KYCSerializer,
    PCCSerializer,
    SkillCertificatesSerializer,
    LocationSerializer,
    ProApplicationStatusSerializer,
)


# ── Helper ─────────────────────────────────────────────────────────────────────

def get_draft_application(user):
    try:
        app = ProApplication.objects.get(user=user)
        if app.status in [
            ProApplication.Status.DRAFT,
            ProApplication.Status.RESUBMISSION_REQUIRED
        ]:
            return app
        return None
    except ProApplication.DoesNotExist:
        return None


# ── Start Application ──────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsFullyVerified])
def become_pro(request):
    user = request.user

    if user.role == 'pro':
        return Response(
            {'error': 'You are already a Pro.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    existing = ProApplication.objects.filter(user=user).first()

    if existing:
        if existing.status == ProApplication.Status.SUBMITTED:
            return Response(
                {'error': 'Your application is already submitted and under review.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if existing.status == ProApplication.Status.UNDER_REVIEW:
            return Response(
                {'error': 'Your application is currently being reviewed by our team.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if existing.status == ProApplication.Status.APPROVED:
            return Response(
                {'error': 'Your application is already approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response({
            'message': 'You have an existing application. Please complete and submit it.',
            'application_id': str(existing.id),
            'status': existing.status
        }, status=status.HTTP_200_OK)

    application = ProApplication.objects.create(user=user)
    return Response({
        'message': 'Application started. Please complete all sections and submit.',
        'application_id': str(application.id),
        'status': application.status
    }, status=status.HTTP_201_CREATED)


# ── Application Status ─────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsFullyVerified])
def application_status(request):
    try:
        app = ProApplication.objects.get(user=request.user)
    except ProApplication.DoesNotExist:
        return Response(
            {'error': 'No application found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    serializer = ProApplicationStatusSerializer(app)
    return Response(serializer.data)


# ── Submit ─────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsFullyVerified])
def submit_pro_application(request):
    try:
        app = ProApplication.objects.get(user=request.user)
    except ProApplication.DoesNotExist:
        return Response(
            {'error': 'No application found. Please start your application first.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if app.status not in [
        ProApplication.Status.DRAFT,
        ProApplication.Status.RESUBMISSION_REQUIRED
    ]:
        return Response(
            {'error': f'Application cannot be submitted at current status: {app.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    app.status       = ProApplication.Status.SUBMITTED
    app.submitted_at = now()
    app.save(update_fields=['status', 'submitted_at'])

    return Response({
        'message': 'Your application has been submitted. Our team will contact you as soon as possible.',
        'status': app.status
    }, status=status.HTTP_200_OK)


# ── Step Base View ─────────────────────────────────────────────────────────────

class BaseStepView(APIView):
    permission_classes = [IsFullyVerified]
    parser_classes     = [MultiPartParser, FormParser]
    serializer_class   = None

    def patch(self, request):
        app = get_draft_application(request.user)
        if not app:
            return Response(
                {'error': 'No editable application found. Start your application first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.serializer_class(app, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Saved successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Step Views ─────────────────────────────────────────────────────────────────

class PersonalInfoView(BaseStepView):
    serializer_class = PersonalInfoSerializer


class ServiceInfoView(BaseStepView):
    serializer_class = ServiceInfoSerializer


class KYCView(BaseStepView):
    serializer_class = KYCSerializer


class PCCView(BaseStepView):
    serializer_class = PCCSerializer


class SkillCertificatesView(BaseStepView):
    serializer_class = SkillCertificatesSerializer


class LocationView(BaseStepView):
    serializer_class = LocationSerializer