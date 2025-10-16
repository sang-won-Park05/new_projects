"""Models for user_table and diary_table based on db_user.sqlite3."""

from django.db import models
from apps.core.models import TimeStampedModel


class User(TimeStampedModel):
    """User information mapped exactly from user_table."""

    seq_id = models.AutoField(primary_key=True, db_column="seq_id")
    email_id = models.EmailField(max_length=255, unique=True, db_column="email_id")
    password_hash = models.CharField(max_length=255, db_column="password_hash")
    username = models.CharField(max_length=100, blank=True, null=True, db_column="username")
    nickname = models.CharField(max_length=100, blank=True, null=True, db_column="nickname")
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created_at"
    )  # TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    last_login_at = models.DateTimeField(
        blank=True, null=True, db_column="last_login_at"
    )

    class Meta:
        db_table = "user_table"
        ordering = ("-created_at",)

    def __str__(self):
        return self.nickname or self.username or self.email_id


class DiaryEntry(TimeStampedModel):
    """Diary entries mapped exactly from diary_table."""

    seq_id = models.AutoField(primary_key=True, db_column="seq_id")
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="diary_entries",
    )
    content = models.TextField(null=False, db_column="content")
    diary_date = models.DateField(null=False, db_column="diary_date")
    image_url = models.CharField(
        max_length=255, blank=True, null=True, db_column="image_url"
    )
    is_deleted = models.CharField(
        max_length=1,
        default="N",
        db_column="is_deleted",
        choices=[("Y", "Yes"), ("N", "No")],
    )

    class Meta:
        db_table = "diary_table"
        ordering = ("-diary_date",)

    def __str__(self):
        return f"Diary {self.seq_id} by user {self.user_id} on {self.diary_date}"
