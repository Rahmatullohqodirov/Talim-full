from django.urls import path
from .views import DashboardView, AdminStatsView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="statistics-dashboard"),
    path("admin/overview/", AdminStatsView.as_view(), name="statistics-admin-overview"),
]
