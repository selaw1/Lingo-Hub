from django.contrib.auth.forms import AdminUserCreationForm as BaseAdminUserCreationForm
from django.contrib.auth.forms import UserChangeForm as BaseUserChangeForm
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from .models import User


class UserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class UserAdminCreationForm(BaseAdminUserCreationForm):
    """Used by the Django admin's "add user" form — adds the
    usable_password field the admin's add_fieldsets expects."""

    class Meta(BaseAdminUserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class UserChangeForm(BaseUserChangeForm):
    class Meta(BaseUserChangeForm.Meta):
        model = User
