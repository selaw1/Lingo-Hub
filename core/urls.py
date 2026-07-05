from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("sessions/", include("sessions.urls")),
    path("attendance/", include("attendance.urls")),
    path("wallet/", include("loyalty.urls")),
    path("", RedirectView.as_view(pattern_name="wallet", permanent=False)),
]
