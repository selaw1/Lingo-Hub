from django.contrib import admin

from .models import Stamp, Tier


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = ("name", "min_stamps", "icon", "order")
    ordering = ("order",)


@admin.register(Stamp)
class StampAdmin(admin.ModelAdmin):
    list_display = ("user", "source", "note", "awarded_by", "created_at")
    list_filter = ("source",)
    search_fields = ("user__username", "note")
    autocomplete_fields = ("user", "attendance", "awarded_by")

    def save_model(self, request, obj, form, change):
        # Manually-awarded stamps default to the admin user who created them
        # if no other awarder was specified.
        if obj.source == "manual" and not obj.awarded_by:
            obj.awarded_by = request.user
        super().save_model(request, obj, form, change)
