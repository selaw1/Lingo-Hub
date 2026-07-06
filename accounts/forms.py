from django.contrib.auth.forms import AdminUserCreationForm as BaseAdminUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from .models import User


class UserCreationForm(BaseUserCreationForm):
    """Public self-registration form. Excludes user_type on purpose — the
    "host" role can only be granted by an admin via the Django admin."""

    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class UserAdminCreationForm(BaseAdminUserCreationForm):
    """Used by the Django admin's "add user" form — adds the
    usable_password field the admin's add_fieldsets expects."""

    class Meta(BaseAdminUserCreationForm.Meta):
        model = User
        fields = ("username", "email", "user_type")


class UserChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = User
