from django.db import models

from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)


# =========================================================
# USER MANAGER
# =========================================================

class UserManager(BaseUserManager):

    def create_user(
        self,
        username,
        phone,
        password=None,
        **extra_fields
    ):

        if not username:
            raise ValueError("Username is required")

        if not phone:
            raise ValueError("Phone number is required")

        user = self.model(
            username=username,
            phone=phone,
            **extra_fields
        )

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(
        self,
        username,
        phone,
        password=None,
        **extra_fields
    ):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError(
                "Superuser must have is_staff=True"
            )

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(
                "Superuser must have is_superuser=True"
            )

        return self.create_user(
            username,
            phone,
            password,
            **extra_fields
        )


# =========================================================
# CUSTOM USER MODEL
# =========================================================

class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("member", "Member"),
    )

    username = models.CharField(
        max_length=150,
        unique=True
    )

    phone = models.CharField(
        max_length=15,
        unique=True
    )

    name = models.CharField(
        max_length=100
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="member"
    )

    is_active = models.BooleanField(
        default=True
    )

    is_staff = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    objects = UserManager()

    USERNAME_FIELD = "username"

    REQUIRED_FIELDS = ["phone"]

    def __str__(self):
        return self.username