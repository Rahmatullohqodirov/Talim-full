from django.urls import path
from .views import DashboardView, AdminStatsView, LogActivityView

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="statistics-dashboard"),
    path("admin/overview/", AdminStatsView.as_view(), name="statistics-admin-overview"),
    path("log-activity/", LogActivityView.as_view(), name="statistics-log-activity"),
]
