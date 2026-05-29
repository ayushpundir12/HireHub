from django.urls import path
from .views import (
    CreateBookingView,
    ClientBookingListView,
    ProBookingListView,
    BookingStatusUpdateView,
    CreateReviewView,
    ProReviewListView,
)

urlpatterns = [
    path('bookings/',                          CreateBookingView.as_view(),       name='booking-create'),
    path('bookings/my/',                       ClientBookingListView.as_view(),   name='booking-client-list'),
    path('bookings/incoming/',                 ProBookingListView.as_view(),      name='booking-pro-list'),
    path('bookings/<uuid:pk>/status/',         BookingStatusUpdateView.as_view(), name='booking-status-update'),
    path('bookings/<uuid:pk>/review/',         CreateReviewView.as_view(),        name='booking-review-create'),
    path('pros/<uuid:pro_id>/reviews/',        ProReviewListView.as_view(),       name='pro-review-list'),
]