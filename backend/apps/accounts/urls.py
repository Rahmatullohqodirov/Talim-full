from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, ProfileDetailView, AdminUserViewSet, SubscriptionPlanListView

router = DefaultRouter()
router.register("admin/users", AdminUserViewSet, basename="admin-users")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", ProfileDetailView.as_view(), name="auth-me"),
    path("plans/", SubscriptionPlanListView.as_view(), name="auth-plans"),
    path("", include(router.urls)),
]
