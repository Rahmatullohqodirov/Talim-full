from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, ProfileDetailView, AdminUserViewSet, SubscriptionPlanListView,
    VerifyEmailView, ResendCodeView, SocialAuthView, SocialConfigView,
    AccountUpdateView, ChangePasswordView,
)

router = DefaultRouter()
router.register("admin/users", AdminUserViewSet, basename="admin-users")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="auth-register"),
    path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
    path("resend-code/", ResendCodeView.as_view(), name="auth-resend-code"),
    path("social/", SocialAuthView.as_view(), name="auth-social"),
    path("social/config/", SocialConfigView.as_view(), name="auth-social-config"),
    path("login/", LoginView.as_view(), name="auth-login"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", ProfileDetailView.as_view(), name="auth-me"),
    path("me/account/", AccountUpdateView.as_view(), name="auth-me-account"),
    path("me/change-password/", ChangePasswordView.as_view(), name="auth-me-change-password"),
    path("plans/", SubscriptionPlanListView.as_view(), name="auth-plans"),
    path("", include(router.urls)),
]
