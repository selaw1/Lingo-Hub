from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "session", "timestamp")
    list_filter = ("session",)
    search_fields = ("user__username", "session__title")
