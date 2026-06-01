from django.urls import path
from .views import ProDashboardKPIView, ProEarningsChartView

urlpatterns = [
    path('dashboard/pro/',          ProDashboardKPIView.as_view(),    name='pro-dashboard-kpi'),
    path('dashboard/pro/earnings/', ProEarningsChartView.as_view(),   name='pro-dashboard-earnings'),
]