from django.db import models
from rest_framework import generics, permissions, viewsets, status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.response import Response
from .models import Profile, SubscriptionPlan
from . import services
from .serializers import (
    RegisterSerializer, ProfileSerializer, UserSerializer, SubscriptionPlanSerializer,
    AdminUserUpdateSerializer, VerifyEmailSerializer, ResendCodeSerializer, SocialAuthSerializer,
    AccountUpdateSerializer, ChangePasswordSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"  # spam-registratsiyaning oldini olish uchun

    def perform_create(self, serializer):
        user = serializer.save()
        services.generate_and_send_verification_code(user)


class VerifyEmailView(APIView):
    """POST /auth/verify-email/  {email, code} — hisobni faollashtiradi va tokenlarni qaytaradi."""
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        code = serializer.validated_data["code"]
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"detail": "Bunday email bilan hisob topilmadi."}, status=400)

        ok, message = services.verify_code(user, code)
        if not ok:
            return Response({"detail": message}, status=400)

        refresh = RefreshToken.for_user(user)
        return Response({"detail": message, "access": str(refresh.access_token), "refresh": str(refresh)})


class ResendCodeView(APIView):
    """POST /auth/resend-code/  {email} — yangi tasdiqlash kodi yuboradi."""
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Xavfsizlik uchun email mavjudligini oshkor qilmaymiz
            return Response({"detail": "Agar bunday email ro'yxatdan o'tgan bo'lsa, kod yuborildi."})
        if not user.email_verified:
            services.generate_and_send_verification_code(user)
        return Response({"detail": "Agar bunday email ro'yxatdan o'tgan bo'lsa, kod yuborildi."})


class SocialAuthView(APIView):
    """POST /auth/social/  {provider: 'google'|'facebook', token} — Google/Facebook orqali kirish.

    Google uchun 'token' — Google Identity Services bergan id_token.
    Facebook uchun 'token' — Facebook Login bergan access_token.
    Bu haqiqiy foydalanuvchilarni qabul qiladi: token Google/Facebook serverida tekshiriladi,
    email allaqachon shu provayder tomonidan tasdiqlangan bo'lgani uchun qo'shimcha kod
    yuborilmaydi."""
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        provider = serializer.validated_data["provider"]
        token = serializer.validated_data["token"]

        if provider == "google":
            if not settings.GOOGLE_CLIENT_ID:
                return Response({"detail": "Google orqali kirish hali sozlanmagan (GOOGLE_CLIENT_ID yo'q)."}, status=503)
            profile = services.verify_google_id_token(token)
        else:
            if not settings.FACEBOOK_APP_ID:
                return Response({"detail": "Facebook orqali kirish hali sozlanmagan (FACEBOOK_APP_ID yo'q)."}, status=503)
            profile = services.verify_facebook_access_token(token)

        if not profile:
            return Response({"detail": "Token tasdiqlanmadi — qayta urinib ko'ring."}, status=400)

        email = profile["email"].strip().lower()
        name = (profile.get("name") or "").strip()
        first = profile.get("first_name") or (name.split(" ")[0] if name else "")
        last = profile.get("last_name") or (" ".join(name.split(" ")[1:]) if name else "")
        user = User.objects.filter(email__iexact=email).first()
        created = user is None
        if created:
            user = User(
                email=email, username=services.unique_username(email), is_active=True, email_verified=True,
                auth_provider=provider, first_name=first[:150], last_name=last[:150],
            )
            user.set_unusable_password()
            user.save()
        else:
            # Parol bilan ro'yxatdan o'tib, emailni tasdiqlamagan bo'lsa ham — Google/Facebook emailni tasdiqlagan
            changed = []
            if not user.is_active:
                user.is_active = True
                changed.append("is_active")
            if not user.email_verified:
                user.email_verified = True
                changed.append("email_verified")
            if not user.first_name and first:
                user.first_name, user.last_name = first[:150], last[:150]
                changed += ["first_name", "last_name"]
            if changed:
                user.save(update_fields=changed)

        refresh = RefreshToken.for_user(user)
        onboarding_done = getattr(getattr(user, "profile", None), "onboarding_completed", False)
        return Response({"access": str(refresh.access_token), "refresh": str(refresh), "created": created,
                         "needs_onboarding": created or not onboarding_done})


class SocialConfigView(APIView):
    """GET /auth/social/config/ — frontend Google/Facebook tugmalari uchun ochiq (maxfiy bo'lmagan) ID'lar.

    Shu sababli kalitlarni faqat backend .env fayliga yozish kifoya."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            "google_client_id": settings.GOOGLE_CLIENT_ID or None,
            "facebook_app_id": settings.FACEBOOK_APP_ID if (settings.FACEBOOK_APP_ID and settings.FACEBOOK_APP_SECRET) else None,
        })


class LoginView(TokenObtainPairView):
    """Login yoki email + parol. Email tasdiqlanmagan bo'lsa, tushunarli javob qaytaradi."""
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"  # parolni brute-force qilishning oldini olish uchun

    def post(self, request, *args, **kwargs):
        data = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)
        ident = str(data.get("username", "")).strip()
        user = None
        if "@" in ident:
            user = User.objects.filter(email__iexact=ident).first()
        else:
            user = User.objects.filter(username__iexact=ident).first()
        if user is not None:
            data["username"] = user.username
            if not user.is_active and user.check_password(str(data.get("password", ""))):
                return Response({
                    "detail": "Email hali tasdiqlanmagan. Pochtangizga yuborilgan kodni kiriting.",
                    "code": "email_not_verified", "email": user.email,
                }, status=403)
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Login yoki parol noto'g'ri.", "code": "invalid_credentials"}, status=401)
        return Response(serializer.validated_data, status=200)


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class AccountUpdateView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /auth/me/account/ — Profil sahifasida ism, familiya, email va interfeys tilini tahrirlash."""
    serializer_class = AccountUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /auth/me/change-password/  {old_password, new_password}"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Parol muvaffaqiyatli yangilandi."})


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
        import secrets
        data = request.data.copy()
        generated = not data.get("password")
        if generated:
            data["password"] = secrets.token_urlsafe(9)
        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Admin yaratgan hisob darhol faol (email tasdiqlash shart emas)
        user.is_active = True
        user.email_verified = True
        user.is_premium = bool(request.data.get("is_premium"))
        user.is_staff = bool(request.data.get("is_staff"))
        user.save(update_fields=["is_active", "email_verified", "is_premium", "is_staff"])
        out = UserSerializer(user).data
        if generated:
            out["temp_password"] = data["password"]  # faqat bir marta ko'rsatiladi
        return Response(out, status=status.HTTP_201_CREATED)

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
