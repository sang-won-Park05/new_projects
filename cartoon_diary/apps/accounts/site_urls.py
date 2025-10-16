"""Site (HTML) routes for account pages."""

from django.urls import path

from .views import SiteSignupView


app_name = "site_accounts"

urlpatterns = [
    # Only simple signup is exposed per requirements
    path("signup/", SiteSignupView.as_view(), name="signup"),
]
