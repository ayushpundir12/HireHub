from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Booking, Review
from .serializers import (
    BookingCreateSerializer,
    BookingListSerializer,
    BookingStatusUpdateSerializer,
    ReviewCreateSerializer,
    ReviewSerializer,
)
from apps.pros.permissions import IsProUser
from .pagination import BookingCursorPagination

from django.core.cache import cache
from .tasks import send_completion_otp, generate_otp



class CreateBookingView(APIView):
    """
    POST /bookings/
    Client creates a booking request.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Inject client from the JWT — never trust client-supplied client_id
        booking = serializer.save(client=request.user)
        return Response(BookingListSerializer(booking).data, status=status.HTTP_201_CREATED)


class ClientBookingListView(ListAPIView):
    """
    GET /bookings/my/?status=completed
    Client sees their own bookings.
    """
    serializer_class   = BookingListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = BookingCursorPagination

    def get_queryset(self):
        qs = Booking.objects.select_related(
            'client', 'pro'
        ).filter(client=self.request.user)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class ProBookingListView(ListAPIView):
    """
    GET /bookings/incoming/?status=pending
    Pro sees their incoming bookings.
    """
    serializer_class   = BookingListSerializer
    permission_classes = [IsAuthenticated, IsProUser]
    pagination_class   = BookingCursorPagination

    def get_queryset(self):
        qs = Booking.objects.select_related(
            'client', 'pro'
        ).filter(pro=self.request.user)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class BookingStatusUpdateView(APIView):
    """
    PATCH /bookings/:id/status/
    Pro updates booking status. State machine enforced.
    """
    permission_classes = [IsAuthenticated, IsProUser]

    def patch(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, pro=request.user)

        serializer = BookingStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        # State machine guard — ask the model if this transition is valid
        if not booking.can_transition_to(new_status):
            return Response(
                {
                    'error': f"Cannot transition from '{booking.status}' to '{new_status}'.",
                    'allowed': Booking.PRO_TRANSITIONS.get(booking.status, []),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = new_status
        booking.save(update_fields=['status', 'updated_at'])

        return Response(BookingListSerializer(booking).data)


class CreateReviewView(APIView):
    """
    POST /bookings/:id/review/
    Client posts a review. Only allowed when booking is completed
    and no review exists yet.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, client=request.user)

        # Guard 1: booking must be completed
        if booking.status != Booking.STATUS_COMPLETED:
            return Response(
                {'error': 'Reviews can only be left for completed bookings.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Guard 2: no duplicate review
        if hasattr(booking, 'review'):
            return Response(
                {'error': 'You have already reviewed this booking.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save review — signal fires automatically to update ProProfile rating
        review = serializer.save(
            booking=booking,
            client=request.user,
            pro=booking.pro,
        )

        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ProReviewListView(ListAPIView):
    """
    GET /pros/:pro_id/reviews/
    Public — anyone can read a pro's reviews.
    """
    serializer_class   = ReviewSerializer
    permission_classes = [AllowAny]
    pagination_class   = BookingCursorPagination

    def get_queryset(self):
        return Review.objects.select_related(
            'client'
        ).filter(pro_id=self.kwargs['pro_id'])



from django.core.cache import cache
from .tasks import send_completion_otp, generate_otp


class RequestCompletionView(APIView):
    """
    POST /bookings/:id/request-completion/
    Pro calls this when the job is physically done.

    What happens:
    1. Validate booking belongs to this pro and is in_progress
    2. Generate a 6-digit OTP
    3. Store OTP in Redis keyed by booking_id (TTL 10 min)
    4. Fire Celery task to SMS the OTP to client's phone
    5. Set status to awaiting_confirmation

    Why store OTP by booking_id not user_id?
    Because the OTP is specific to THIS booking transaction.
    A user could have multiple active bookings — keying by booking_id
    ensures there's no collision between them.
    """
    permission_classes = [IsAuthenticated, IsProUser]

    def post(self, request, pk):
        booking = get_object_or_404(
            Booking, pk=pk, pro=request.user
        )

        # Guard: must be in_progress to request completion
        if booking.status != Booking.STATUS_IN_PROGRESS:
            return Response(
                {
                    'error': f"Booking must be 'in_progress' to request completion.",
                    'current_status': booking.status,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Guard: client must have a phone number
        if not booking.client.phone_number:
            return Response(
                {'error': 'Client has no phone number on file. Cannot send OTP.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate and store OTP in Redis — 10 minute TTL
        otp       = generate_otp()
        cache_key = f"completion_otp:{booking.id}"
        cache.set(cache_key, otp, timeout=600)

        # Fire SMS task asynchronously
        send_completion_otp.delay(
            str(booking.id),
            booking.client.phone_number,
            otp,
        )

        # Update status
        booking.status = Booking.STATUS_AWAITING_CONFIRMATION
        booking.save(update_fields=['status', 'updated_at'])

        return Response({
            'message': 'OTP sent to client\'s phone. Ask the client for the code.',
            'status':  booking.status,
        })


class ConfirmCompletionView(APIView):
    """
    POST /bookings/:id/confirm-completion/
    Pro submits the OTP the client verbally gave them.

    What happens:
    1. Validate booking is awaiting_confirmation
    2. Fetch OTP from Redis
    3. Compare submitted OTP
    4. If valid → mark completed, delete OTP from Redis
    5. Signal fires → ProProfile avg_rating + total_jobs updated

    Why does the PRO submit the OTP and not the client?
    The pro is physically present with the client. The client reads
    the OTP off their phone and tells the pro. The pro enters it into
    their app. This confirms the client was present and satisfied.
    It's the same UX as Uber/Urban Company job confirmation.
    """
    permission_classes = [IsAuthenticated, IsProUser]

    def post(self, request, pk):
        booking = get_object_or_404(
            Booking, pk=pk, pro=request.user
        )

        # Guard: must be awaiting confirmation
        if booking.status != Booking.STATUS_AWAITING_CONFIRMATION:
            return Response(
                {
                    'error': "Booking is not awaiting confirmation.",
                    'current_status': booking.status,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        submitted_otp = request.data.get('otp')
        if not submitted_otp:
            return Response(
                {'error': 'OTP is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache_key  = f"completion_otp:{booking.id}"
        cached_otp = cache.get(cache_key)

        # OTP expired
        if not cached_otp:
            return Response(
                {
                    'error': 'OTP has expired. Please request a new one.',
                    'action': f'POST /bookings/{booking.id}/request-completion/',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # OTP wrong
        if submitted_otp != cached_otp:
            return Response(
                {'error': 'Invalid OTP. Please check with the client.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ OTP valid — mark completed
        booking.status = Booking.STATUS_COMPLETED
        booking.save(update_fields=['status', 'updated_at'])

        # Clean up OTP from Redis — single use
        cache.delete(cache_key)

        # Signal fires automatically here →
        # apps/bookings/signals.py → update_pro_rating runs
        # No explicit call needed

        return Response({
            'message': 'Job marked as completed successfully.',
            'status':  booking.status,
        })