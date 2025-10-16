# cartoon_diary/scripts/test_integration_all.py
from __future__ import annotations

import os
from typing import List
from dotenv import load_dotenv

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(CURR_DIR)
REPO_ROOT = os.path.dirname(PROJECT_DIR)
load_dotenv(os.path.join(REPO_ROOT, ".env"))
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

from cartoon_diary.integrations.openai_prompt import generate_prompt_from_diary
from cartoon_diary.integrations.openai_imagegen import (
    generate_image_url,
    fetch_bytes,
    compose_grid,
)

DEFAULT_DIARY_TEXT = (
    "오늘 아침 창밖을 보니 비가 부슬부슬 내리고 있었다.\n"
    "서둘러 우산을 챙기며 신발을 신는데, 괜히 마음도 조금 급해졌다.\n"
    "버스 정류장에 도착했을 땐 바닥이 온통 물웅덩이라 신발 끝이 축축해졌다.\n"
    "괜히 찜찜했지만, 회사 근처 카페에서 따뜻한 커피를 한 모금 마시니\n"
    "금세 마음이 풀어졌다 ☕️\n"
    "젖은 우산을 털고 자리에 앉아 컴퓨터를 켜니\n"
    "비 오는 아침치고 꽤 기분 좋은 하루가 시작되는 것 같다."
)

def main() -> None:
    diary_text = DEFAULT_DIARY_TEXT.strip()

    print("1) Generating prompt from diary...")
    prompt = generate_prompt_from_diary(diary_text=diary_text)
    panels = prompt.get("panels", [])
    if len(panels) != 4:
        raise RuntimeError(f"Expected 4 panels, got {len(panels)}")
    for p in panels:
        print(f"   - idx={p['index']} | caption={p.get('caption','')}")

    print("\n2) Generating 4 images (DALL·E 3)...")
    imgs: List[bytes] = []
    for p in panels:
        desc = p.get("description", "")
        url = generate_image_url(prompt=desc)
        imgs.append(fetch_bytes(url=url))

    print("\n3) Composing 2x2 grid...")
    grid_bytes = compose_grid(imgs)
    out_path = os.path.abspath(os.path.join(REPO_ROOT, "test_comic_grid.png"))
    with open(out_path, "wb") as f:
        f.write(grid_bytes)

    print(f"\n✅ Done. Saved grid: {out_path}")

if __name__ == "__main__":
    main()
