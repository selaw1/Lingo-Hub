from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserAdminCreationForm, UserChangeForm
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserAdminCreationForm
    form = UserChangeForm
    model = User
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional info", {"fields": ("gender", "date_of_birth", "mobile_number")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Additional info", {"fields": ("email", "gender", "date_of_birth", "mobile_number")}),
    )
