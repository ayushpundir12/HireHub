import razorpay
import hmac
import hashlib
import logging
import json

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from apps.bookings.models import Booking
from .models import Payment
from .serializers import InitiatePaymentSerializer, VerifyPaymentSerializer

logger = logging.getLogger(__name__)

# Razorpay client — initialized once at module level
client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


class InitiatePaymentView(APIView):
    """
    POST /payments/initiate/

    Creates a Razorpay Order and returns order_id + key_id to frontend.
    Frontend uses these to open the Razorpay checkout modal.

    Why return key_id to frontend?
    Razorpay checkout needs your public key_id (not secret) to
    initialize. key_id is safe to expose — it's like a public key.
    Only key_secret must stay on the server.

    Amount in Razorpay is always in smallest unit:
    INR → paise (1 INR = 100 paise)
    So ₹90 = 9000 paise
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking_id = serializer.validated_data['booking_id']
        try:
            booking = Booking.objects.select_related('client', 'pro').get(id=booking_id)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Security: only the client of this booking can pay
        if booking.client != request.user:
            return Response(
                {'error': 'You do not have permission to pay for this booking.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            # Create Razorpay order
            # receipt is a short reference you can use in your dashboard
            order = client.order.create({
                'amount':          int(booking.amount * 100),  # paise
                'currency':        'INR',
                'receipt':         f"booking_{str(booking.id)[:8]}",
                'notes': {
                    'booking_id': str(booking.id),
                    'client_id':  str(request.user.id),
                    'pro_id':     str(booking.pro.id),
                }
            })

            # Store order reference in DB
            payment = Payment.objects.create(
                booking           = booking,
                user              = request.user,
                razorpay_order_id = order['id'],
                amount            = booking.amount,
                currency          = 'INR',
                status            = Payment.STATUS_PENDING,
            )

            return Response({
                'order_id':   order['id'],
                'amount':     order['amount'],       # in paise
                'currency':   order['currency'],
                'key_id':     settings.RAZORPAY_KEY_ID,  # safe to expose
                'booking_id': str(booking.id),
                'name':       'HireHub',
                'description': f"{booking.category} service booking",
                'prefill': {
                    'name':    request.user.full_name,
                    'contact': request.user.phone_number or '',
                }
            })

        except razorpay.errors.BadRequestError as e:
            logger.error(f"Razorpay order creation failed for booking {booking_id}: {e}")
            return Response(
                {'error': 'Payment initiation failed. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class VerifyPaymentView(APIView):
    """
    POST /payments/verify/

    Frontend calls this AFTER Razorpay checkout succeeds.
    Razorpay gives the frontend three values:
      - razorpay_order_id
      - razorpay_payment_id
      - razorpay_signature

    We verify the signature using HMAC-SHA256 before trusting the payment.

    Why verify signature?
    The frontend could be tampered with. Someone could fake a
    successful payment response. The signature is computed using
    your key_secret which only your server knows — it cannot be faked.

    Signature formula (from Razorpay docs):
    HMAC_SHA256(order_id + "|" + payment_id, key_secret)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id   = serializer.validated_data['razorpay_order_id']
        payment_id = serializer.validated_data['razorpay_payment_id']
        signature  = serializer.validated_data['razorpay_signature']

        # Fetch our payment record
        try:
            payment = Payment.objects.select_related('booking').get(
                razorpay_order_id=order_id
            )
        except Payment.DoesNotExist:
            return Response(
                {'error': 'Payment record not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Security: ensure this payment belongs to the requesting user
        if payment.user != request.user:
            return Response(
                {'error': 'Permission denied.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Verify signature — this is the critical security step
        body          = f"{order_id}|{payment_id}"
        expected_sig  = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            # Signature mismatch — reject
            logger.warning(
                f"Razorpay signature mismatch for order {order_id}. "
                f"Possible tampered request."
            )
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=['status', 'updated_at'])

            return Response(
                {'error': 'Payment verification failed. Invalid signature.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Signature valid — mark payment and booking as paid
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature  = signature
        payment.status              = Payment.STATUS_SUCCEEDED
        payment.save(update_fields=[
            'razorpay_payment_id', 'razorpay_signature',
            'status', 'updated_at'
        ])

        booking                = payment.booking
        booking.payment_status = Booking.PAYMENT_PAID
        booking.status         = Booking.STATUS_CONFIRMED
        booking.save(update_fields=['payment_status', 'status', 'updated_at'])

        logger.info(f"Payment verified for booking {booking.id}")

        return Response({
            'message':    'Payment verified successfully.',
            'booking_id': str(booking.id),
            'status':     booking.status,
        })


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """
    POST /payments/webhook/

    Razorpay calls this as a backup when payment events occur.
    Even if the frontend crashes after payment, this ensures
    the booking gets marked as paid.

    Webhook signature verification:
    Razorpay signs webhook payload with your webhook_secret
    using SHA256. We verify before processing.

    Idempotency:
    We check razorpay_event_id before processing to avoid
    updating the booking twice if Razorpay retries the webhook.
    """
    authentication_classes = []
    permission_classes     = [AllowAny]

    def post(self, request):
        # Get webhook secret from settings
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)

        if webhook_secret:
            # Verify webhook signature
            received_sig = request.headers.get('X-Razorpay-Signature', '')
            body         = request.body

            expected_sig = hmac.new(
                webhook_secret.encode(),
                body,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_sig, received_sig):
                logger.warning("Razorpay webhook signature verification failed.")
                return Response({'error': 'Invalid signature.'}, status=400)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid payload.'}, status=400)

        event_id   = payload.get('id', '')
        event_type = payload.get('event', '')

        # Idempotency — don't process same event twice
        if Payment.objects.filter(razorpay_event_id=event_id).exists():
            logger.info(f"Duplicate webhook event {event_id} ignored.")
            return Response({'received': True})

        if event_type == 'payment.captured':
            self._handle_payment_captured(payload, event_id)

        elif event_type == 'payment.failed':
            self._handle_payment_failed(payload)

        return Response({'received': True})

    def _handle_payment_captured(self, payload, event_id):
        try:
            order_id = payload['payload']['payment']['entity']['order_id']
            payment  = Payment.objects.select_related('booking').get(
                razorpay_order_id=order_id
            )
        except (KeyError, Payment.DoesNotExist):
            logger.error("Webhook: payment not found.")
            return

        # Skip if already verified via /verify/ endpoint
        if payment.status == Payment.STATUS_SUCCEEDED:
            logger.info(f"Webhook: payment {order_id} already succeeded. Skipping.")
            return

        payment.status            = Payment.STATUS_SUCCEEDED
        payment.razorpay_event_id = event_id
        payment.save(update_fields=['status', 'razorpay_event_id', 'updated_at'])

        booking                = payment.booking
        booking.payment_status = Booking.PAYMENT_PAID
        booking.status         = Booking.STATUS_CONFIRMED
        booking.save(update_fields=['payment_status', 'status', 'updated_at'])

        logger.info(f"Webhook: booking {booking.id} confirmed via payment.captured.")

    def _handle_payment_failed(self, payload):
        try:
            order_id = payload['payload']['payment']['entity']['order_id']
            payment  = Payment.objects.get(razorpay_order_id=order_id)
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=['status', 'updated_at'])
        except (KeyError, Payment.DoesNotExist):
            logger.error("Webhook: failed payment not found.")


class PaymentStatusView(APIView):
    """
    GET /payments/booking/<booking_id>/
    Client checks payment status for a booking.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        booking = Booking.objects.filter(
            id=booking_id, client=request.user
        ).first()

        if not booking:
            return Response(
                {'error': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        payment = Payment.objects.filter(
            booking=booking
        ).order_by('-created_at').first()

        return Response({
            'booking_id':     str(booking.id),
            'payment_status': booking.payment_status,
            'booking_status': booking.status,
            'payment': {
                'id':                   str(payment.id),
                'razorpay_order_id':    payment.razorpay_order_id,
                'razorpay_payment_id':  payment.razorpay_payment_id,
                'amount':               payment.amount,
                'currency':             payment.currency,
                'status':               payment.status,
            } if payment else None
        })