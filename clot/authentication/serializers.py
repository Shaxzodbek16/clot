from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import User, Address


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    phone_number = serializers.CharField(
        validators=[
            RegexValidator(
                regex=r"^\+998[0-9]{9}$",
                message="Invalid phone number format. Must be in format: +998901234567",
            )
        ]
    )

    class Meta:
        model = User
        fields = ("phone_number", "password", "first_name")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)


class CompleteProfileSerializer(serializers.Serializer):
    user_slug = serializers.CharField()
    age = serializers.IntegerField(min_value=0)
    gender = serializers.ChoiceField(choices=User.GENDER_CHOICES)


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)

    @staticmethod
    def validate_new_password(value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long"
            )
        return value


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "slug",
            "phone_number",
            "first_name",
            "last_name",
            "profile_picture",
            "age",
            "gender",
            "date_joined",
            "is_active",
        )
        read_only_fields = ("slug", "phone_number", "date_joined")


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "profile_picture", "age", "gender")

    def validate_age(self, value):
        if value < 0:
            raise serializers.ValidationError("Age cannot be negative")
        return value
