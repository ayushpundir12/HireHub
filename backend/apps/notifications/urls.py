from django.urls import path
from .views import (
    NotificationListView,
    MarkNotificationReadView,
    MarkAllReadView,
    UnreadCountView,
)

urlpatterns = [
    path('notifications/',                    NotificationListView.as_view(),      name='notification-list'),
    path('notifications/read-all/',           MarkAllReadView.as_view(),           name='notification-read-all'),
    path('notifications/unread-count/',       UnreadCountView.as_view(),           name='notification-unread-count'),
    path('notifications/<uuid:pk>/read/',     MarkNotificationReadView.as_view(),  name='notification-read'),
]