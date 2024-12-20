from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import re

from slugify import slugify

from .extensions import generate_unique_slug


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    @staticmethod
    def _validate_phone_number(phone_number):
        pattern = r"^\+998[0-9]{9}$"
        if not re.match(pattern, phone_number):
            raise ValueError(
                "Invalid phone number format. Must be in format: +998901234567"
            )

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The Phone Number field must be set")

        self._validate_phone_number(phone_number)

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)  # Changed default to True

        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = (("male", "Male"), ("female", "Female"))

    username = None
    phone_number = models.CharField(
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\+998[0-9]{9}$",
                message="Invalid phone number format. Must be in format: +998901234567",
            )
        ],
        error_messages={"unique": "A user with this phone number already exists."},
    )

    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/%Y/%m/%d", blank=True, null=True
    )
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    slug = models.CharField(max_length=160, unique=True, blank=True, null=True)
    age = models.PositiveIntegerField(default=0)
    gender = models.CharField(
        max_length=6, choices=GENDER_CHOICES, default=GENDER_CHOICES[0][0]
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["first_name"]  # Added first_name as required

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        db_table = "User"
        ordering = ["-date_joined"]

    def get_gender_display(self):
        return self.gender.title()

    def __str__(self):
        return f"{self.phone_number} - {self.first_name} - {self.get_gender_display()}"

    def get_full_name(self):
        full_name = f"{self.first_name}"
        if self.last_name:
            full_name = f"{full_name} {self.last_name}"
        return full_name.strip()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = f"{self.phone_number}-{self.first_name}"
            self.slug = slugify(base_slug)
        super().save(*args, **kwargs)


class Address(models.Model):
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    slug = models.CharField(unique=True, blank=True, null=True, max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_unique_slug(self, self.street_address)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.street_address}, {self.city}"

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        db_table = "addresses"
        ordering = ["-created_at"]


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("order_placed", "Order Placed"),
        ("order_confirmed", "Order Confirmed"),
        ("order_shipped", "Order Shipped"),
        ("order_delivered", "Order Delivered"),
        ("order_cancelled", "Order Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    # order = models.ForeignKey("payments.Order", on_delete=models.CASCADE, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.CharField(unique=True, blank=True, null=True, max_length=160)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.slug = generate_unique_slug(self, self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.user.phone_number}"

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        db_table = "notifications"
        ordering = ["-created_at"]


class OneTimePassword(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    passcode = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.phone_number}: {self.passcode}"

    class Meta:
        verbose_name = "One Time Password"
        verbose_name_plural = "One Time Passwords"
        db_table = "otp"
        ordering = ["-created_at"]
