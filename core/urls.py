from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("sessions/", include("sessions.urls")),
    path("attendance/", include("attendance.urls")),
    path("", include("loyalty.urls")),  # Lingo Card home at /
]
