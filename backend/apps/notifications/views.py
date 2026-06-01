from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from django.shortcuts import get_object_or_404

from .models import Notification
from .serializers import NotificationSerializer


class NotificationCursorPagination(CursorPagination):
    page_size          = 20
    ordering           = '-created_at'
    cursor_query_param = 'cursor'


class NotificationListView(ListAPIView):
    """
    GET /notifications/
    GET /notifications/?unread=true   → only unread

    Returns the user's notifications newest first.
    Also returns unread_count in the response for the bell badge.
    """
    serializer_class   = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = NotificationCursorPagination

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)

        if self.request.query_params.get('unread') == 'true':
            qs = qs.filter(is_read=False)

        return qs

    def list(self, request, *args, **kwargs):
        response      = super().list(request, *args, **kwargs)
        unread_count  = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()

        # Inject unread_count into paginated response
        response.data['unread_count'] = unread_count
        return response


class MarkNotificationReadView(APIView):
    """
    PATCH /notifications/:id/read/
    Mark a single notification as read.
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notification = get_object_or_404(
            Notification, pk=pk, user=request.user
        )
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'status': 'marked as read'})


class MarkAllReadView(APIView):
    """
    POST /notifications/read-all/
    Mark all notifications as read in one query.

    Why .update() instead of looping and saving each one?
    .update() is a single SQL UPDATE statement regardless of
    how many rows there are. Looping would fire N queries.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)

        return Response({
            'status':  'all notifications marked as read',
            'updated': count,
        })


class UnreadCountView(APIView):
    """
    GET /notifications/unread-count/
    Lightweight endpoint for the bell badge.
    Frontend polls this every 30 seconds.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        return Response({'unread_count': count})