from django.urls import path

from . import views

urlpatterns = [
    path("", views.wallet_view, name="wallet"),
    path("export/", views.export_view, name="export_attendance"),
]
