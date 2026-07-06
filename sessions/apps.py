from django.apps import AppConfig


class SessionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sessions"
    # Custom label: django.contrib.sessions already claims the "sessions"
    # app label, so this app (also named "sessions") needs a distinct one
    # to avoid an "Application labels aren't unique" startup error.
    label = "class_sessions"
    verbose_name = "Class Sessions"
