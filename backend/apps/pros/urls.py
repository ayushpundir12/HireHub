from django.urls import path
from .views import (
    ProListView,
    ProDetailView,
    ProOwnProfileView,
    CategoryListView,
)

urlpatterns = [
    # Public discovery
    path('pros/',              ProListView.as_view(),      name='pro-list'),
    path('pros/<uuid:pk>/',    ProDetailView.as_view(),    name='pro-detail'),
    path('categories/',        CategoryListView.as_view(), name='category-list'),

    # Pro self-service (auth required, role=pro)
    path('pro/profile/',       ProOwnProfileView.as_view(), name='pro-own-profile'),
]