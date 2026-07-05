from django.urls import path

from . import views

urlpatterns = [
    path("", views.session_list_view, name="session_list"),
    path("create/", views.session_create_view, name="session_create"),
    path("<int:session_id>/qr/", views.session_qr_view, name="session_qr"),
    path(
        "<int:session_id>/qr/image/",
        views.session_qr_image_view,
        name="session_qr_image",
    ),
]
