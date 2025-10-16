# cartoon_diary/integrations/openai_prompt.py
from __future__ import annotations
import os, json, re
from typing import Dict, List, Any

import requests
from dotenv import load_dotenv

# ── Django 의존 없는 실행을 위해 IntegrationError를 안전하게 로드 ──
try:
    from apps.core.exceptions import IntegrationError  # Django 환경에서 사용
except Exception:  # 테스트/단독 실행 시 대체
    class IntegrationError(Exception):
        """Lightweight fallback used when Django apps are not loaded."""
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
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in .env")

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}

# ------------------------
# 글로벌 스타일 (항상 유지)
# ------------------------
GLOBAL_STYLE = (
    "[GLOBAL STYLE]\n"
    "A monochrome pencil sketch in the style of a newspaper editorial cartoon, drawn by an amateur artist.\n"
    "The drawing has rough graphite lines, light cross-hatching, minimal detail, and no color.\n"
    "Each panel is separated by clean white gutters and thin black frames.\n"
    "The characters have simple, naive proportions, like a stick-figure with expressive faces.\n"
    "White background, high contrast pencil texture, no digital effects, no color.\n"
    "Captions appear under each panel.\n"
    "Overall tone: lighthearted, slice-of-life, minimalist."
)

# (선택) 네거티브 스타일을 항상 추가하고 싶으면 여기에 정의하고 USER_TEMPLATE 지시문에 포함하세요.
NEGATIVE_STYLE = (
    "[NEGATIVE STYLE]\n"
    "no color, no watercolor, no digital painting, no photorealism, no shading, no 3D render, no anime,\n"
    "no text artifacts, no watermark, no background clutter, no detailed environments,\n"
    "no colored tones, no realistic lighting, no signature, no photographic effects."
)

# ------------------------
# 프롬프트 지시문
# ------------------------
SYSTEM_MSG = (
    "You convert a Korean diary entry into a 4-panel comic plan.\n"
    "Return STRICT JSON with keys: model, panels.\n"
    "panels is an array of 4 objects, each with: index(0..3), description(English, visual detail), caption(Korean, short).\n"
    "VERY IMPORTANT:\n"
    " - Each panel's description MUST BEGIN with the exact GLOBAL STYLE block, then the scene description.\n"
    " - Optionally, you MAY append the NEGATIVE STYLE lines after GLOBAL STYLE for safety.\n"
    " - Descriptions must stay concise and image-model friendly.\n"
)

USER_TEMPLATE = """Diary text (Korean):
---
{diary_text}
---

GLOBAL STYLE (use this EXACTLY at the beginning of every description):
---
{global_style}
---

NEGATIVE STYLE (optional; you may append after GLOBAL STYLE):
---
{negative_style}
---

Return ONLY valid JSON:
{{
  "model": "{model}",
  "panels": [
    {{
      "index": 0,
      "description": "{global_style}\\n<concise English scene prompt for panel 0>\\n{negative_style}",
      "caption": "<Korean short caption for panel 0>"
    }},
    {{
      "index": 1,
      "description": "{global_style}\\n<concise English scene prompt for panel 1>\\n{negative_style}",
      "caption": "<Korean short caption for panel 1>"
    }},
    {{
      "index": 2,
      "description": "{global_style}\\n<concise English scene prompt for panel 2>\\n{negative_style}",
      "caption": "<Korean short caption for panel 2>"
    }},
    {{
      "index": 3,
      "description": "{global_style}\\n<concise English scene prompt for panel 3>\\n{negative_style}",
      "caption": "<Korean short caption for panel 3>"
    }}
  ]
}}
"""

# ------------------------
# 내부 유틸
# ------------------------
@retry(exceptions=(requests.RequestException,), tries=2)
def _chat_completion(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{OPENAI_BASE_URL}/chat/completions"
    resp = requests.post(url, json=payload, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.json()

def _extract_json(text: str) -> Dict[str, Any]:
    """LLM 응답에서 JSON 부분만 안전하게 추출."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if m:
        text = m.group(1)
    if not text.strip().startswith("{"):
        m2 = re.search(r"(\{.*\})", text, flags=re.S)
        if m2:
            text = m2.group(1)
    return json.loads(text)

def _normalize_panels(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    panels = data.get("panels") or []
    if len(panels) != 4:
        raise IntegrationError("Prompt must contain exactly 4 panels.")
    norm: List[Dict[str, Any]] = []
    for i, p in enumerate(panels):
        idx = int(p.get("index", i))
        desc = str(p.get("description", "")).strip()
        cap = str(p.get("caption", "")).strip()
        if not desc or not cap:
            raise IntegrationError("Panel description/caption cannot be empty.")
        # 안전 장치: description이 GLOBAL STYLE로 시작하는지 보정
        if not desc.startswith(GLOBAL_STYLE.splitlines()[0]):
            desc = f"{GLOBAL_STYLE}\n{desc}"
        norm.append({"index": idx, "description": desc, "caption": cap})
    norm.sort(key=lambda x: x["index"])
    # 인덱스 보정(0..3)
    for i, p in enumerate(norm):
        p["index"] = i
    return norm

# ------------------------
# 외부 진입점
# ------------------------
def generate_prompt_from_diary(*, diary_text: str) -> Dict[str, Any]:
    """
    일기 텍스트를 4컷 만화 기획 JSON으로 변환.
    각 패널의 description은 항상 GLOBAL STYLE로 시작.
    Returns:
      {"model": "<chat-model>", "panels": [{"index":0,"description":"...","caption":"..."}, ...]}
    """
    if not diary_text or not diary_text.strip():
        raise IntegrationError("Diary text is empty.")

    user_msg = USER_TEMPLATE.format(
        diary_text=diary_text.strip(),
        model=OPENAI_CHAT_MODEL,
        global_style=GLOBAL_STYLE.replace('"', '\\"'),
        negative_style=NEGATIVE_STYLE.replace('"', '\\"'),
    )

    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_MSG},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.4,
    }

    try:
        data = _chat_completion(payload)
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        parsed = _extract_json(content)
        panels = _normalize_panels(parsed)
        return {"model": parsed.get("model", OPENAI_CHAT_MODEL), "panels": panels}
    except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
        raise IntegrationError(f"OpenAI prompt generation failed: {e}") from e
