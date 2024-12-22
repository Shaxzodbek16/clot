from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import TokenError
from rest_framework import permissions, status
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import views
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from enum import Enum


class SMSMessage(Enum):
    REGISTRATION = "registration"
    FORGOT_PASSWORD = "forgot_password"


from .models import OneTimePassword, User
from .serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    CompleteProfileSerializer,
    LoginSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .extensions import send_sms, generate_code


class AuthView(views.APIView):
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["phone_number", "first_name", "last_name"]
    search_fields = ["phone_number", "first_name", "last_name"]

    @staticmethod
    def _handle_otp_verification(phone_number, otp_code):
        otp = OneTimePassword.objects.filter(
            user__phone_number=phone_number,
            passcode=otp_code,
            created_at__gte=timezone.now() - timedelta(minutes=5),
        ).first()

        if not otp:
            return None
        return otp.user

    @staticmethod
    def _generate_tokens(user):
        refresh = RefreshToken.for_user(user)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}

    def post(self, request, action):
        handlers = {
            "register": self._handle_register,
            "verify_otp": self._handle_verify_otp,
            "complete_profile": self._handle_complete_profile,
            "login": self._handle_login,
            "forgot_password": self._handle_forgot_password,
            "reset_password": self._handle_reset_password,
        }

        handler = handlers.get(action)
        if not handler:
            return Response(
                {"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST
            )

        return handler(request)

    @staticmethod
    def _handle_register(request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        if User.objects.filter(phone_number=phone_number).exists():
            return Response(
                {"error": "User with this phone number already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save(is_active=False)

        otp_code = generate_code()
        OneTimePassword.objects.filter(user=user).delete()
        OneTimePassword.objects.create(user=user, passcode=otp_code)
        send_sms(
            phone_number=user.phone_number,
            name=user.first_name,
            code=otp_code,
            type=SMSMessage.REGISTRATION.value,
        )

        return Response(
            {"message": "OTP sent successfully.", "user_slug": user.slug},
            status=status.HTTP_201_CREATED,
        )

    def _handle_verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        otp_code = serializer.validated_data["otp_code"]

        user = self._handle_otp_verification(phone_number, otp_code)
        if not user:
            return Response(
                {"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.save()
        OneTimePassword.objects.filter(user=user).delete()

        tokens = self._generate_tokens(user)
        return Response(
            {"message": "OTP verified successfully", "user_slug": user.slug, **tokens},
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _handle_complete_profile(request):
        serializer = CompleteProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_slug = serializer.validated_data.get("user_slug")
        user = get_object_or_404(User, slug=user_slug)

        user.age = serializer.validated_data["age"]
        user.gender = serializer.validated_data["gender"]
        user.save()

        return Response(
            {"message": "Profile completed successfully", "user_slug": user.slug}
        )

    def _handle_login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        password = serializer.validated_data["password"]

        user = authenticate(phone_number=phone_number, password=password)
        if not user:
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "User account is not active"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = self._generate_tokens(user)
        return Response(
            {"message": "Login successful", "user_slug": user.slug, **tokens}
        )

    @staticmethod
    def _handle_forgot_password(request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        user = get_object_or_404(User, phone_number=phone_number)

        # Generate and send OTP
        otp_code = generate_code()
        OneTimePassword.objects.create(user=user, passcode=otp_code)
        send_sms(
            phone_number=user.phone_number,
            name=user.first_name,
            code=otp_code,
            type=SMSMessage.FORGOT_PASSWORD.value,
        )

        return Response({"message": "OTP sent successfully", "user_slug": user.slug})

    def _handle_reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.validated_data["phone_number"]
        otp_code = serializer.validated_data["otp_code"]
        new_password = serializer.validated_data["new_password"]

        user = self._handle_otp_verification(phone_number, otp_code)
        if not user:
            return Response(
                {"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Reset password and delete OTP
        user.set_password(new_password)
        user.save()
        OneTimePassword.objects.filter(user=user).delete()

        tokens = self._generate_tokens(user)
        return Response(
            {"message": "Password reset successfully", "user_slug": user.slug, **tokens}
        )


class UserDetailsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, slug=None):
        try:
            if self.request.path.endswith("/me/"):
                serializer = UserSerializer(request.user)
                return Response(serializer.data)

            if not slug and request.query_params.get("all"):
                if not request.user.is_staff:
                    return Response(
                        {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                    )

                queryset = User.objects.all()

                search = request.query_params.get("search")
                if search:
                    queryset = queryset.filter(
                        Q(phone_number__icontains=search)
                        | Q(first_name__icontains=search)
                        | Q(last_name__icontains=search)
                    )

                gender = request.query_params.get("gender")
                if gender:
                    queryset = queryset.filter(gender=gender)

                age = request.query_params.get("age")
                if age:
                    queryset = queryset.filter(age=age)

                ordering = request.query_params.get("ordering", "-date_joined")
                if ordering:
                    queryset = queryset.order_by(ordering)

                page = int(request.query_params.get("page", 1))
                page_size = int(request.query_params.get("page_size", 10))
                start = (page - 1) * page_size
                end = start + page_size

                users = queryset[start:end]
                total = queryset.count()

                serializer = UserSerializer(users, many=True)
                return Response(
                    {
                        "results": serializer.data,
                        "total": total,
                        "page": page,
                        "total_pages": (total + page_size - 1) // page_size,
                        "page_size": page_size,
                    }
                )

            if slug:
                if not request.user.is_staff:
                    return Response(
                        {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                    )
                user = get_object_or_404(User, slug=slug)
                serializer = UserSerializer(user)
                return Response(serializer.data)

            return Response(
                {"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, slug=None):
        try:
            if self.request.path.endswith("/me/"):
                user = request.user
            else:
                if not request.user.is_staff:
                    return Response(
                        {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                    )
                user = get_object_or_404(User, slug=slug)
            serializer = UserUpdateSerializer(user, data=request.data)
            if serializer.is_valid():
                if "phone_number" in serializer.validated_data:
                    del serializer.validated_data["phone_number"]
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, slug=None):
        """Partially update user details"""
        try:
            # Update current user for /me/ endpoint
            if self.request.path.endswith("/me/"):
                user = request.user
            else:
                # Update specific user (staff only)
                if not request.user.is_staff:
                    return Response(
                        {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                    )
                user = get_object_or_404(User, slug=slug)

            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                # Prevent updating phone_number
                if "phone_number" in serializer.validated_data:
                    del serializer.validated_data["phone_number"]
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, slug=None):
        """Deactivate user account"""
        try:
            # Delete current user for /me/ endpoint
            if self.request.path.endswith("/me/"):
                user = request.user
            else:
                # Delete specific user (staff only)
                if not request.user.is_staff:
                    return Response(
                        {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
                    )
                user = get_object_or_404(User, slug=slug)

            # Soft delete - deactivate user
            user.is_active = False
            user.save()

            return Response({"message": "User account deactivated successfully"})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Get refresh token
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            # Optional: Blacklist all tokens for this user
            # Uncomment if you want to log out from all devices
            """
            tokens = OutstandingToken.objects.filter(user_id=request.user.id)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
            """

            return Response(
                {"message": "Successfully logged out"}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LogoutAllView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            tokens = OutstandingToken.objects.filter(user_id=request.user.id)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)

            return Response(
                {"message": "Successfully logged out from all devices"},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Refresh access token using refresh token
        """
        try:
            # Get refresh token from request
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Verify and generate new tokens
            refresh = RefreshToken(refresh_token)

            data = {
                "access": str(refresh.access_token),
                "refresh": str(refresh),  # New refresh token
            }

            return Response(data, status=status.HTTP_200_OK)

        except TokenError:
            return Response(
                {"error": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
