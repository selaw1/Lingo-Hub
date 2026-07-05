from django.conf import settings
from django.db import models

from sessions.models import Session


class Attendance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "session")
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.user} @ {self.session} ({self.timestamp})"
