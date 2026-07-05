from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from common.utils import make_uuid


class GenderChoices(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"


class UserTypeChoices(models.TextChoices):
    STUDENT = "student", "Student"
    HOST = "host", "Host"


class User(AbstractUser):
    "User model"

    id = models.UUIDField(primary_key=True, default=make_uuid)
    email = models.EmailField("Email address", unique=True)
    user_type = models.CharField(
        choices=UserTypeChoices.choices, max_length=20, default=UserTypeChoices.STUDENT
    )
    gender = models.CharField(choices=GenderChoices.choices, max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    mobile_number = PhoneNumberField(blank=True, null=True)
