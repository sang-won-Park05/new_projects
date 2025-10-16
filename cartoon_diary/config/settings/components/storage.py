"""Storage defaults and overrides."""

import os


# AWS S3 설정
USE_S3 = os.getenv("DEFAULT_FILE_STORAGE") == "storages.backends.s3.S3Storage"

if USE_S3:
    # AWS S3 credentials
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "ap-northeast-2")

    # S3 파일 설정
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",  # 1일 캐시
    }
    AWS_DEFAULT_ACL = "public-read"  # 파일을 공개로 설정
    AWS_S3_FILE_OVERWRITE = False  # 같은 이름 파일 덮어쓰기 방지
    AWS_QUERYSTRING_AUTH = False  # URL에 서명 제거

    # 미디어 파일 URL 설정
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"

    DEFAULT_FILE_STORAGE = "storages.backends.s3.S3Storage"
else:
    # 로컬 파일 시스템 사용
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

STORAGES = {
    "default": {
        "BACKEND": DEFAULT_FILE_STORAGE,
        "OPTIONS": {
            "location": os.getenv("DJANGO_MEDIA_ROOT") if not USE_S3 else None,
        } if not USE_S3 else {},
    },
    # Required by Django 4.2+ system check (staticfiles.E005)
    "staticfiles": {
        "BACKEND": os.getenv(
            "DJANGO_STATICFILES_STORAGE",
            "django.contrib.staticfiles.storage.StaticFilesStorage",
        )
    },
}
