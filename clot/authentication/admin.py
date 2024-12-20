from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.admin import UserAdmin
from .models import User, Address, Notification, OneTimePassword


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "phone_number",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "gender",
        "age",
        "date_joined",
        "profile_picture_preview",
    )
    list_filter = ("is_active", "is_staff", "gender", "date_joined")
    search_fields = ("phone_number", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "updated_at", "slug")

    fieldsets = (
        (
            "Personal Info",
            {
                "fields": (
                    "phone_number",
                    "first_name",
                    "last_name",
                    "profile_picture",
                    "age",
                    "gender",
                    "slug",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "fields": ("date_joined", "updated_at", "last_login"),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone_number",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.profile_picture.url,
            )
        return "No Image"

    profile_picture_preview.short_description = "Profile Picture"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "street_address",
        "city",
        "state",
        "zip_code",
        "is_default",
        "user_link",
        "created_at",
    )
    list_filter = ("city", "state", "is_default", "created_at")
    search_fields = (
        "street_address",
        "city",
        "state",
        "zip_code",
        "user__phone_number",
        "user__first_name",
    )
    readonly_fields = ("slug", "created_at", "updated_at")
    raw_id_fields = ("user",)

    fieldsets = (
        (
            "Address Information",
            {
                "fields": (
                    "street_address",
                    "city",
                    "state",
                    "zip_code",
                    "is_default",
                    "slug",
                )
            },
        ),
        ("User Information", {"fields": ("user",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def user_link(self, obj):
        # Fix: Use the correct URL pattern name based on your app name
        url = reverse("admin:authentication_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.phone_number)

    user_link.short_description = "User"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "user_link", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("title", "message", "user__phone_number", "user__first_name")
    readonly_fields = ("slug", "created_at")
    raw_id_fields = ("user",)

    fieldsets = (
        (
            "Notification Details",
            {"fields": ("title", "message", "type", "is_read", "slug")},
        ),
        ("User Information", {"fields": ("user",)}),
        ("Timestamps", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    actions = ["mark_as_read", "mark_as_unread"]

    def user_link(self, obj):
        url = reverse("admin:authentication_user_change", args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.phone_number)

    user_link.short_description = "User"

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)

    mark_as_unread.short_description = "Mark selected notifications as unread"


admin.site.register(OneTimePassword)
