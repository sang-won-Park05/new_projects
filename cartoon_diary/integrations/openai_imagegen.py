# cartoon_diary/integrations/openai_imagegen.py
from __future__ import annotations

import os, io
from typing import Any, Dict, List, Tuple

import requests
from PIL import Image
from dotenv import load_dotenv

# ── Django 미로딩 환경에서도 동작하도록 예외 안전 처리 ──
try:
    from apps.core.exceptions import IntegrationError  # Django 실행 시
except Exception:
    class IntegrationError(Exception):
        """Fallback used when Django apps are not loaded."""
        pass

from .retry import retry

# ── .env 로드: 리포지토리 루트와 프로젝트 디렉터리 모두 시도 ──
CURR_DIR = os.path.dirname(os.path.abspath(__file__))           # .../cartoon_diary/integrations
PROJECT_DIR = os.path.dirname(CURR_DIR)                          # .../cartoon_diary
REPO_ROOT = os.path.dirname(PROJECT_DIR)                         # .../SKN16-4th-1Team
load_dotenv(os.path.join(REPO_ROOT, ".env"))
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")   # DALL·E 3
OPENAI_IMAGE_SIZE  = os.getenv("OPENAI_IMAGE_SIZE",  "1024x1024")  # DALL·E 3은 1024만 지원

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in .env")

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}

# =====================================================
# 1) 이미지 생성 (DALL·E 3)
# =====================================================
@retry(exceptions=(requests.RequestException,), tries=2)
def _image_generate(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{OPENAI_BASE_URL}/images/generations"
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=90)
    resp.raise_for_status()
    return resp.json()

def generate_image_url(*, prompt: str, model: str | None = None, size: str | None = None) -> str:
    """DALL·E 3로 이미지 생성 후 URL 반환"""
    payload = {
        "model": model or OPENAI_IMAGE_MODEL,
        "prompt": prompt,
        "n": 1,
        "size": size or OPENAI_IMAGE_SIZE,
    }
    try:
        data = _image_generate(payload)
        url = (data.get("data") or [{}])[0].get("url")
        if not url:
            raise IntegrationError("Image generation did not return a valid URL.")
        return url
    except requests.RequestException as e:
        raise IntegrationError(f"OpenAI image generation failed: {e}") from e

# =====================================================
# 2) 이미지 다운로드
# =====================================================
@retry(exceptions=(requests.RequestException,), tries=2)
def fetch_bytes(*, url: str) -> bytes:
    """이미지 URL에서 바이트 다운로드"""
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.content
    except requests.RequestException as e:
        raise IntegrationError(f"Failed to download image: {e}") from e

# =====================================================
# 3) 4컷 그리드 합성 (2x2)
# =====================================================
def _ensure_rgba(img: Image.Image) -> Image.Image:
    return img.convert("RGBA") if img.mode != "RGBA" else img

def _uniform_size(images: List[Image.Image]) -> Tuple[int, int]:
    """가장 작은 이미지 크기에 맞춰 전체 크기 통일"""
    ws = [im.width for im in images]
    hs = [im.height for im in images]
    return min(ws), min(hs)

def compose_grid(
    images_bytes: List[bytes],
    grid: Tuple[int, int] = (2, 2),
    resize_to: Tuple[int, int] | None = (512, 512),
) -> bytes:
    """
    여러 이미지를 2x2 그리드로 합성해 PNG 바이트로 반환.
    resize_to=(512,512) → 1024 이미지를 최종 축소 저장.
    """
    expected = grid[0] * grid[1]
    if len(images_bytes) != expected:
        raise IntegrationError(f"Grid expects {expected} images, got {len(images_bytes)}.")

    imgs: List[Image.Image] = []
    for b in images_bytes:
        img = Image.open(io.BytesIO(b))
        imgs.append(_ensure_rgba(img))

    w, h = _uniform_size(imgs)
    norm = [im.resize((w, h), Image.LANCZOS) for im in imgs]

    rows, cols = grid
    canvas = Image.new("RGBA", (cols * w, rows * h), (255, 255, 255, 0))
    for i, im in enumerate(norm):
        r, c = divmod(i, cols)
        canvas.paste(im, (c * w, r * h))

    if resize_to:
        canvas = canvas.resize(resize_to, Image.LANCZOS)

    out = io.BytesIO()
    canvas.save(out, format="PNG")
    return out.getvalue()
