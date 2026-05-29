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