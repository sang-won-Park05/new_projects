"""Custom user model compatible with SQLite DB (user_table)."""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class UserManager(BaseUserManager):
    """Custom manager for User model using email_id as the unique identifier."""

    def create_user(self, email_id, password=None, **extra_fields):
        if not email_id:
            raise ValueError("Users must have an email address")
        email_id = self.normalize_email(email_id)
        user = self.model(email_id=email_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email_id, password=None, **extra_fields):
        """Create and save a superuser with given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email_id, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """User model reflecting db_user.sqlite3 user_table."""

    seq_id = models.BigAutoField(primary_key=True)  # INTEGER PK AUTOINCREMENT
    email_id = models.EmailField(unique=True, null=False)  # TEXT UNIQUE NOT NULL
    password = models.CharField(max_length=128, null=False)  # Django 기본 password 해시
    username = models.CharField(max_length=100, blank=True, null=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    # Django permission fields (admin compatibility)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email_id"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        db_table = "user_table"  # match SQLite table name

    def __str__(self):
        return self.nickname or self.username or self.email_id
