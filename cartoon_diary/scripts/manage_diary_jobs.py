# ── Django setup (공통) ─────────────────────────────────────────────
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cartoon_diary.config.settings")
django.setup()
# ───────────────────────────────────────────────────────────────────

"""Command-line helper to trigger diary generation jobs."""

import argparse
from apps.generation.pipelines import trigger_cartoon_generation

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trigger cartoon generation for a diary entry"
    )
    parser.add_argument("diary_entry_id", type=int, help="DiaryEntry primary key")
    parser.add_argument(
        "--text",
        dest="diary_text_override",
        default=None,
        help="Override diary raw text (if provided, it takes precedence over DB content)",
    )
    args = parser.parse_args()

    trigger_cartoon_generation(
        diary_entry_id=args.diary_entry_id,
        diary_text_override=args.diary_text_override,  # None이면 DB의 content 사용
    )

    print(f"🪄 Enqueued generation for diary #{args.diary_entry_id}")
    if args.diary_text_override:
        print("   ↳ Using override text from CLI")

if __name__ == "__main__":
    main()
