# apps/generation/tasks.py
"""Celery tasks orchestrating the diary → prompt → image pipeline."""

from __future__ import annotations
from django.utils import timezone
from django.core.files.base import ContentFile
from celery import chain, shared_task

from apps.core.exceptions import IntegrationError
from apps.diaries.models import DiaryEntry
from .models import Cartoon, CartoonPanel, Prompt
from .services import mark_cartoon_failed

# 새 integrations 모듈 사용
from integrations.openai_prompt import generate_prompt_from_diary
from integrations.openai_imagegen import generate_image_url, fetch_bytes, compose_grid


@shared_task
def generate_prompt_task(ctx: dict) -> dict:
    """
    ctx = {
      "diary_entry_id": int,
      "cartoon_id": int,
      "prompt_id": None|int,
      "diary_text_override": None|str,  # ← 프론트에서 온 일기 텍스트 (우선 사용)
    }
    """
    try:
        diary = DiaryEntry.objects.get(pk=ctx["diary_entry_id"])

        # -----------------------------------------------------------
        # ✨ 프론트엔드 연결 지점
        # - 프론트에서 일기 텍스트를 보내줄 때 이 키로 넣어주세요.
        # - 예) pipelines.trigger_cartoon_generation(..., diary_text_override=request.POST["diaryText"])
        # - 임시로 경로만 표기:
        #   ("일기장텍스트경로")
        # -----------------------------------------------------------
        diary_text = (ctx.get("diary_text_override") or diary.content or "").strip()
        if not diary_text:
            raise IntegrationError("Diary text is empty.")

        prompt_body = generate_prompt_from_diary(diary_text=diary_text)

        prompt = Prompt.objects.create(
            diary_entry=diary,
            body=prompt_body,
            model=prompt_body.get("model", "gpt-4o-mini"),
        )

        # 진행 상태 갱신
        Cartoon.objects.filter(pk=ctx["cartoon_id"]).update(status=Cartoon.Status.RUNNING)

        ctx["prompt_id"] = prompt.pk
        return ctx

    except Exception as e:
        try:
            cartoon = Cartoon.objects.get(pk=ctx.get("cartoon_id"))
            mark_cartoon_failed(cartoon=cartoon, reason=str(e))
        finally:
            raise


@shared_task
def generate_panels_task(ctx: dict) -> dict:
    """프롬프트를 받아 4컷 이미지를 생성하고 저장"""
    try:
        prompt = Prompt.objects.get(pk=ctx["prompt_id"])
        cartoon = Cartoon.objects.get(pk=ctx["cartoon_id"])

        panels = prompt.body.get("panels") or []
        if len(panels) != 4:
            raise IntegrationError("Prompt must contain 4 panels")

        for p in panels:
            index = int(p.get("index"))
            description = p.get("description", "")
            caption = p.get("caption", "")

            image_url = generate_image_url(prompt=description)
            image_bytes = fetch_bytes(url=image_url)

            panel = CartoonPanel.objects.create(
                cartoon=cartoon,
                index=index,
                caption=caption,
            )
            panel.image.save(f"panel_{index}.png", ContentFile(image_bytes), save=True)

        return ctx

    except Exception as e:
        try:
            cartoon = Cartoon.objects.get(pk=ctx.get("cartoon_id"))
            mark_cartoon_failed(cartoon=cartoon, reason=str(e))
        finally:
            raise


@shared_task
def compose_grid_task(ctx: dict) -> dict:
    """생성된 4컷을 2x2 그리드로 합성"""
    try:
        cartoon = Cartoon.objects.get(pk=ctx["cartoon_id"])

        panel_bytes = []
        for panel in cartoon.panels.order_by("index"):
            if not panel.image:
                raise IntegrationError("Panel image missing for grid composition")
            panel.image.open("rb")
            try:
                panel_bytes.append(panel.image.read())
            finally:
                panel.image.close()

        grid_bytes = compose_grid(panel_bytes)  # 기본 2x2, 내부에서 512로 리사이즈 가능
        cartoon.grid_image.save("grid.png", ContentFile(grid_bytes), save=False)
        cartoon.status = Cartoon.Status.SUCCEEDED
        cartoon.completed_at = timezone.now()
        cartoon.save(update_fields=["grid_image", "status", "completed_at", "updated_at"])
        return ctx

    except Exception as e:
        try:
            cartoon = Cartoon.objects.get(pk=ctx.get("cartoon_id"))
            mark_cartoon_failed(cartoon=cartoon, reason=str(e))
        finally:
            raise


@shared_task
def run_generation_pipeline(diary_entry_id: int, diary_text_override: str | None = None) -> None:
    """
    파이프라인 시작 태스크
    - Cartoon 레코드를 생성(QUEUED)
    - 컨텍스트에 diary_text_override(프론트 전달 텍스트)를 함께 싣고 비동기 체인 실행
    """
    cartoon = Cartoon.objects.create(
        diary_entry_id=diary_entry_id,
        status=Cartoon.Status.QUEUED,
    )

    ctx = {
        "diary_entry_id": diary_entry_id,
        "cartoon_id": cartoon.pk,
        "prompt_id": None,
        # -----------------------------------------------------------
        # ✨ 프론트엔드 연결 지점
        # - 프론트 텍스트를 여기로 전달하면 generate_prompt_task에서 우선 사용됨.
        # - 지금은 경로만 명시:
        #   diary_text_override = ("일기장텍스트경로")
        # -----------------------------------------------------------
        "diary_text_override": diary_text_override,
    }

    chain(
        generate_prompt_task.s(ctx),
        generate_panels_task.s(),
        compose_grid_task.s(),
    ).apply_async()
