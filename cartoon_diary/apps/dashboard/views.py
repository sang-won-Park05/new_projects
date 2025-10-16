"""Dashboard views."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from apps.diaries.models import DiaryEntry


class DashboardView(LoginRequiredMixin, TemplateView):
    # Use a new template name to avoid any stale template caching issues
    template_name = "dashboard/home.html"

    def post(self, request, *args, **kwargs):
        """Handle inline diary submission from dashboard.

        Creates or updates today's diary entry for the current user.
        """
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
            messages.warning(request, "내용을 입력해 주세요.")
            return redirect("/dashboard/")

        entry, _created = DiaryEntry.objects.get_or_create(user=request.user, date=date)
        entry.title = title
        entry.content = content
        entry.save()
        messages.success(request, "일기가 저장되었습니다.")
        return redirect("/dashboard/")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        ctx["today"] = today
        # Preload today's entry if exists
        ctx["today_entry"] = (
            DiaryEntry.objects.filter(user=self.request.user, date=today).first()
        )
        return ctx
