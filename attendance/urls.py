from django.urls import path

from . import views

urlpatterns = [
    path("scan/", views.scan_page_view, name="scan_page"),
    path("scan/submit/", views.scan_view, name="scan"),
    path("scan/error/", views.scan_error_view, name="scan_error"),
    path(
        "sessions/<uuid:session_id>/attendees/",
        views.session_attendees_view,
        name="session_attendees",
    ),
]
