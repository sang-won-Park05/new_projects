"""Abstract base models matching db_user.sqlite3 structure."""

from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model reflecting common timestamp fields from db_user.sqlite3.
    Includes created_at (from user_table) and optional updated_at for consistency.
    """

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column="created_at",
        help_text="Record creation timestamp.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column="updated_at",
        help_text="Last updated timestamp.",
    )

    class Meta:
        abstract = True
