"""Profile-related models (db_user.sqlite3에는 profile_table이 존재하지 않음)."""

from django.db import models
from apps.core.models import TimeStampedModel
from apps.generation.models import User


# ⚠️ 현재 db_user.sqlite3에는 profile_table이 존재하지 않습니다.
# 따라서 Profile 모델은 주석 처리하여 DB 구조를 그대로 유지합니다.
# 필요 시 향후 확장을 위해 아래 정의를 참고하세요.

# class Profile(TimeStampedModel):
#     """User profile (not present in db_user.sqlite3)."""
#
#     user = models.OneToOneField(
#         User,
#         on_delete=models.CASCADE,
#         related_name="profile",
#         db_column="user_id",
#     )
#     nickname = models.CharField(max_length=50, blank=True, null=_
