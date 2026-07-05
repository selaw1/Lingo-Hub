from django.conf import settings
from django.db import models

from common.utils import make_uuid


class Session(models.Model):
    id = models.UUIDField(primary_key=True, default=make_uuid)
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
