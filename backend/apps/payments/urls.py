from django.urls import path
from .views import (
    InitiatePaymentView,
    VerifyPaymentView,
    RazorpayWebhookView,
    PaymentStatusView,
)

urlpatterns = [
    path('payments/initiate/',                  InitiatePaymentView.as_view(),  name='payment-initiate'),
    path('payments/verify/',                    VerifyPaymentView.as_view(),    name='payment-verify'),
    path('payments/webhook/',                   RazorpayWebhookView.as_view(),  name='razorpay-webhook'),
    path('payments/booking/<uuid:booking_id>/', PaymentStatusView.as_view(),    name='payment-status'),
]