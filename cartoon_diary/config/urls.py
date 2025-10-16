"""Root URL configuration for the cartoon diary project."""

from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # First screen: Login page
    path("", auth_views.LoginView.as_view(template_name="common/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),

    # Web app: dashboard (requires login via view mixin)
    path("dashboard/", include("apps.dashboard.urls")),

    # Site account pages (signup, ID/PW 찾기)
    path("accounts/", include("apps.accounts.site_urls")),

    # Existing API endpoints
    path("api/auth/", include("apps.accounts.urls")),
    path("api/profile/", include("apps.profiles.urls")),
    path("api/cartoons/", include("apps.generation.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
