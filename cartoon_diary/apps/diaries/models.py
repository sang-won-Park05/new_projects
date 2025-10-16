"""Diary models mapped to db_user.sqlite3 diary_table."""

from django.db import models
from apps.core.models import TimeStampedModel
from apps.accounts.models import User  # our custom user model linked to user_table


class Diary(TimeStampedModel):
    """Model reflecting the exact structure of diary_table."""

    seq_id = models.AutoField(primary_key=True, db_column="seq_id")  # INTEGER PK AUTOINCREMENT
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="diaries",
        db_column="user_id",
    )
    content = models.TextField(null=False, db_column="content")
    diary_date = models.DateField(null=False, db_column="diary_date")
    image_url = models.CharField(
        max_length=255, blank=True, null=True, db_column="image_url"
    )
    is_deleted = models.CharField(
        max_length=1,
        choices=[("Y", "Yes"), ("N", "No")],
        default="N",
        db_column="is_deleted",
    )

    class Meta:
        db_table = "diary_table"
        ordering = ("-diary_date",)

    def __str__(self):
        return f"Diary {self.seq_id} ({self.diary_date}) by {self.user.email_id}"
