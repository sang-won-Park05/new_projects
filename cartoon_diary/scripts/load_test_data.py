# ── Django setup (공통) ─────────────────────────────────────────────
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cartoon_diary.config.settings")
django.setup()
# ───────────────────────────────────────────────────────────────────

"""Utility script to load seed data for development."""

from datetime import date
from django.contrib.auth import get_user_model

# 프로젝트 서비스 함수 명이 환경마다 다를 수 있어 두 가지 모두 지원
try:
    from apps.diaries.services import create_diary_entry as save_diary_entry
except ImportError:  # 기존 이름이 그대로라면
    from apps.diaries.services import save_diary_entry  # type: ignore

def run() -> None:
    User = get_user_model()

    # 데모 유저 생성/업데이트
    user, _ = User.objects.get_or_create(
        email="demo@example.com",
        defaults={"username": "demo"},
    )
    user.set_password("demo1234")
    user.save()

    # 오늘 날짜 일기 한 건 저장
    entry = save_diary_entry(
        user=user,
        entry_date=date.today(),
        content=(
            "비가 와서 급히 우산을 챙겨 나섰다. "
            "정류장에서 신발이 조금 젖었지만 회사 근처 카페에서 따뜻한 커피를 마시니 마음이 풀렸다. "
            "젖은 우산을 말리고 자리에 앉아 일을 시작했다."
        ),
        mood="calm",
        tags=["rain", "coffee"],
    )

    print("✅ Seed user created/updated: demo@example.com / demo1234")
    print(f"✅ Seed diary saved: id={getattr(entry, 'id', None)} date={getattr(entry, 'date', None)}")

if __name__ == "__main__":
    run()
