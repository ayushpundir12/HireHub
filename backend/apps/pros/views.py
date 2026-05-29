from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from .models import ProProfile
from .serializers import (
    ProPublicSerializer,
    ProOwnProfileSerializer,
    ProProfileUpdateSerializer,
)
from .permissions import IsProUser
from .cache import (
    discovery_cache_key, profile_cache_key,
    invalidate_pro_cache, DISCOVERY_TTL, PROFILE_TTL,
)
from .pagination import ProCursorPagination


# ── Discovery ─────────────────────────────────────────────────────────────────

class ProListView(ListAPIView):
    """
    GET /pros/?category=plumber&city=dubai&state=dubai&rating_min=4.0&available=true
    Public. Redis-cached per unique param combo. Cursor-paginated.
    """
    serializer_class   = ProPublicSerializer
    pagination_class   = ProCursorPagination
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        params = {
            k: request.query_params.get(k)
            for k in ['category', 'city', 'state', 'rating_min', 'available', 'cursor']
        }
        cache_key = discovery_cache_key(params)
        cached    = cache.get(cache_key)

        if cached:
            return Response(cached)

        queryset   = self._build_queryset(params)
        page       = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        response   = self.get_paginated_response(serializer.data)

        # Cache the paginated response data
        cache.set(cache_key, response.data, timeout=DISCOVERY_TTL)
        return response

    def _build_queryset(self, params):
        qs = ProProfile.objects.select_related('user').filter(
            user__role='pro'
        )
        if params.get('category'):
            qs = qs.filter(category=params['category'])
        if params.get('city'):
            qs = qs.filter(city__iexact=params['city'])
        if params.get('state'):
            qs = qs.filter(state__iexact=params['state'])
        if params.get('rating_min'):
            qs = qs.filter(avg_rating__gte=params['rating_min'])
        if params.get('available') == 'true':
            qs = qs.filter(is_available=True)
        return qs


class ProDetailView(RetrieveAPIView):
    """
    GET /pros/<id>/
    Public. Redis-cached per pro id.
    """
    serializer_class   = ProPublicSerializer
    permission_classes = [AllowAny]

    def retrieve(self, request, *args, **kwargs):
        pro_id    = self.kwargs['pk']
        cache_key = profile_cache_key(pro_id)
        cached    = cache.get(cache_key)

        if cached:
            return Response(cached)

        pro        = get_object_or_404(
            ProProfile.objects.select_related('user'), pk=pro_id
        )
        serializer = self.get_serializer(pro)
        cache.set(cache_key, serializer.data, timeout=PROFILE_TTL)
        return Response(serializer.data)


# ── Pro Self-Service ───────────────────────────────────────────────────────────

class ProOwnProfileView(APIView):
    """
    GET  /pro/profile/  → fetch own profile for edit form
    PATCH /pro/profile/ → update bio, rate, category, availability, etc.
    """
    permission_classes = [IsAuthenticated, IsProUser]

    def get(self, request):
        pro = get_object_or_404(ProProfile, user=request.user)
        return Response(ProOwnProfileSerializer(pro).data)

    def patch(self, request):
        pro        = get_object_or_404(ProProfile, user=request.user)
        serializer = ProProfileUpdateSerializer(pro, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Bust cache so discovery + detail return fresh data
        invalidate_pro_cache(pro.id)

        return Response(ProOwnProfileSerializer(pro).data)


# ── Categories ────────────────────────────────────────────────────────────────

class CategoryListView(APIView):
    """
    GET /categories/
    Returns all categories with active pro count.
    Cached 15 min.
    """
    permission_classes = [AllowAny]

    CACHE_KEY = 'categories:all'
    TTL       = 900  # 15 min

    def get(self, request):
        cached = cache.get(self.CACHE_KEY)
        if cached:
            return Response(cached)

        from .models import CATEGORY_CHOICES
        from django.db.models import Count

        counts = (
            ProProfile.objects
            .filter(user__role='pro')
            .values('category')
            .annotate(pro_count=Count('id'))
        )
        count_map = {row['category']: row['pro_count'] for row in counts}

        data = [
            {
                'value':     slug,
                'label':     label,
                'pro_count': count_map.get(slug, 0),
            }
            for slug, label in CATEGORY_CHOICES
        ]
        cache.set(self.CACHE_KEY, data, timeout=self.TTL)
        return Response(data)