from django.db import models
from rest_framework import generics, permissions, viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from .models import Profile, SubscriptionPlan
from .serializers import (
    RegisterSerializer, ProfileSerializer, UserSerializer, SubscriptionPlanSerializer,
    AdminUserUpdateSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"  # spam-registratsiyaning oldini olish uchun


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"  # parolni brute-force qilishning oldini olish uchun


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class SubscriptionPlanListView(generics.ListAPIView):
    """GET /auth/plans/ — mavjud obuna rejalari (Billing sahifasi uchun)."""
    queryset = SubscriptionPlan.objects.all().order_by("price_usd")
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class AdminUserViewSet(viewsets.ModelViewSet):
    """GET/POST/PATCH/DELETE /auth/admin/users/ — admin uchun foydalanuvchilarni to'liq boshqarish.

    DELETE haqiqiy o'chirishni emas, balki foydalanuvchini faolsizlantirishni (is_active=False)
    bajaradi — bu bog'liq statistikalar, to'lovlar va sessiyalarni buzmaydi.
    """
    queryset = User.objects.select_related("profile").order_by("-date_joined")
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "post", "patch", "delete", "head"]
    filterset_fields = ["is_premium", "is_staff", "is_active"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RegisterSerializer
        if self.request.method == "PATCH":
            return AdminUserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                models.Q(username__icontains=search)
                | models.Q(email__icontains=search)
                | models.Q(phone__icontains=search)
            )
        return qs

    def create(self, request, *args, **kwargs):
        from rest_framework import status
        data = request.data.copy()
        data.setdefault("password", User.objects.make_random_password())
        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data)

    def destroy(self, request, *args, **kwargs):
        from rest_framework import status
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)
