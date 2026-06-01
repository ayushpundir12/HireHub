from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from django.db.models import Sum, Count, Q
from django.db.models.functions import (
    TruncDay, TruncWeek, TruncMonth
)
from django.utils import timezone
from datetime import timedelta

from apps.bookings.models import Booking
from apps.pros.models import ProProfile
from apps.pros.permissions import IsProUser

DASHBOARD_TTL = 120  # 2 minutes cache


class ProDashboardKPIView(APIView):
    """
    GET /dashboard/pro/

    Returns all KPI numbers for the pro dashboard header.
    Cached 2 minutes per pro.

    Thought process for acceptance_rate:
    acceptance_rate = jobs accepted / jobs received
    "Accepted" means status ever moved past pending
    (confirmed, in_progress, awaiting_confirmation, completed)
    "Received" means all bookings ever sent to this pro
    """
    permission_classes = [IsAuthenticated, IsProUser]

    def get(self, request):
        pro      = request.user
        cache_key = f"dashboard:kpi:{pro.id}"
        cached    = cache.get(cache_key)

        if cached:
            return Response(cached)

        # All bookings received by this pro
        all_bookings = Booking.objects.filter(pro=pro)

        # Completed bookings only
        completed = all_bookings.filter(status=Booking.STATUS_COMPLETED)

        # Earnings — sum of completed booking amounts
        earnings = completed.aggregate(
            total=Sum('amount')
        )['total'] or 0

        # Acceptance rate
        total_received = all_bookings.count()
        total_accepted = all_bookings.filter(
            status__in=[
                Booking.STATUS_CONFIRMED,
                Booking.STATUS_IN_PROGRESS,
                Booking.STATUS_AWAITING_CONFIRMATION,
                Booking.STATUS_COMPLETED,
            ]
        ).count()

        acceptance_rate = (
            round((total_accepted / total_received) * 100, 1)
            if total_received > 0 else 0
        )

        # Pending bookings — needs pro action
        pending_count = all_bookings.filter(
            status=Booking.STATUS_PENDING
        ).count()

        # Avg rating + total jobs already maintained on ProProfile via signal
        try:
            profile = ProProfile.objects.get(user=pro)
            avg_rating = float(profile.avg_rating)
            total_jobs = profile.total_jobs
        except ProProfile.DoesNotExist:
            avg_rating = 0
            total_jobs = 0

        data = {
            'total_jobs':      total_jobs,
            'total_earnings':  float(earnings),
            'avg_rating':      avg_rating,
            'acceptance_rate': acceptance_rate,
            'pending_bookings': pending_count,
        }

        cache.set(cache_key, data, timeout=DASHBOARD_TTL)
        return Response(data)


class ProEarningsChartView(APIView):
    """
    GET /dashboard/pro/earnings/?range=daily|weekly|monthly

    Returns time-series earnings data for the chart.
    Each point has a date label and earnings amount.

    Why TruncDay/TruncWeek/TruncMonth?
    These are Django database functions that group timestamps
    by time period entirely in SQL — no Python loops needed.
    The DB does the heavy lifting, returns one row per period.

    Daily  → last 30 days
    Weekly → last 12 weeks
    Monthly → last 12 months
    """
    permission_classes = [IsAuthenticated, IsProUser]

    RANGE_CONFIG = {
        'daily':   {'trunc': TruncDay,   'delta': timedelta(days=30),      'format': '%Y-%m-%d'},
        'weekly':  {'trunc': TruncWeek,  'delta': timedelta(weeks=12),     'format': '%Y-W%W'},
        'monthly': {'trunc': TruncMonth, 'delta': timedelta(days=365),     'format': '%Y-%m'},
    }

    def get(self, request):
        pro        = request.user
        range_type = request.query_params.get('range', 'weekly')

        if range_type not in self.RANGE_CONFIG:
            return Response(
                {'error': 'Invalid range. Use daily, weekly, or monthly.'},
                status=400
            )

        cache_key = f"dashboard:earnings:{pro.id}:{range_type}"
        cached    = cache.get(cache_key)
        if cached:
            return Response(cached)

        config    = self.RANGE_CONFIG[range_type]
        trunc_fn  = config['trunc']
        since     = timezone.now() - config['delta']
        fmt       = config['format']

        # Push grouping + aggregation entirely to database
        rows = (
            Booking.objects
            .filter(
                pro=pro,
                status=Booking.STATUS_COMPLETED,
                updated_at__gte=since,
            )
            .annotate(period=trunc_fn('updated_at'))
            .values('period')
            .annotate(earnings=Sum('amount'))
            .order_by('period')
        )

        # Format for frontend charting library
        data = {
            'range': range_type,
            'points': [
                {
                    'period':   row['period'].strftime(fmt),
                    'earnings': float(row['earnings']),
                }
                for row in rows
            ],
            'total': sum(row['earnings'] for row in rows),
        }

        cache.set(cache_key, data, timeout=DASHBOARD_TTL)
        return Response(data)