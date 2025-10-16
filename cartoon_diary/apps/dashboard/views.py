"""Dashboard views."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from apps.diaries.models import DiaryEntry
from apps.generation.selectors import get_latest_cartoon_for_entry
from apps.generation.pipelines import trigger_cartoon_generation


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def post(self, request, *args, **kwargs):
        """Save/update today's diary and trigger generation."""
        content = (request.POST.get("content") or "").strip()
        title = (request.POST.get("title") or "").strip()
        date_str = request.POST.get("date")
        date = timezone.localdate()
        if date_str:
            try:
                date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                pass

        if not content:
            messages.warning(request, "내용을 입력해주세요.")
            return redirect("/dashboard/")

        entry, _created = DiaryEntry.objects.get_or_create(user=request.user, date=date)
        entry.title = title
        entry.content = content
        entry.save()

        try:
            trigger_cartoon_generation(diary_entry_id=entry.id)
            messages.success(request, "만화 생성 작업을 시작했어요. 잠시 후 결과가 표시됩니다.")
        except Exception:
            messages.info(request, "일기를 저장했어요. 생성 작업은 나중에 다시 시도할 수 있어요.")
        return redirect("/dashboard/")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        ctx["today"] = today
        entry = DiaryEntry.objects.filter(user=self.request.user, date=today).first()
        ctx["today_entry"] = entry
        if entry:
            ctx["latest_cartoon"] = get_latest_cartoon_for_entry(diary_entry_id=entry.id)
        return ctx

