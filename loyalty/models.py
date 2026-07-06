from django.conf import settings
from django.db import models

from attendance.models import Attendance
from common.utils import make_uuid


class Tier(models.Model):
    id = models.UUIDField(primary_key=True, default=make_uuid)
    name = models.CharField(max_length=50)  # Bronze, Silver, Gold...
    min_stamps = models.IntegerField()
    icon = models.CharField(max_length=100, blank=True)  # emoji or static path
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["min_stamps"]

    def __str__(self):
        return self.name


class Stamp(models.Model):
    SOURCE_CHOICES = [
        ("attendance", "Attendance"),
        ("event", "Special Event"),
        ("manual", "Manual Award"),
        ("streak", "Streak Bonus"),
    ]
    id = models.UUIDField(primary_key=True, default=make_uuid)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="stamps"
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    attendance = models.ForeignKey(Attendance, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=255, blank=True)
    awarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stamps_awarded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.get_source_display()} ({self.created_at:%Y-%m-%d})"
