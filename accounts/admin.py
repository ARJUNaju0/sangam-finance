from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    model = User

    list_display = (
        "id",
        "username",
        "phone",
        "role",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "role",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "phone",
        "name",
    )

    ordering = (
        "username",
    )

    readonly_fields = (
        "created_at",
    )

    fieldsets = (

        (None, {
            "fields": (
                "username",
                "phone",
                "password",
            )
        }),

        ("Personal Info", {
            "fields": (
                "name",
            )
        }),

        ("Roles & Permissions", {
            "fields": (
                "role",
                "is_staff",
                "is_active",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

        ("Important Dates", {
            "fields": (
                "last_login",
                "created_at",
            )
        }),
    )

    add_fieldsets = (

        (None, {
            "classes": ("wide",),

            "fields": (
                "username",
                "phone",
                "name",
                "password1",
                "password2",
                "role",
                "is_staff",
                "is_active",
            ),
        }),
    )