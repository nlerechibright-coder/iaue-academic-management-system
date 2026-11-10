# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model for Academic Management System.
    
    Inherits all standard fields from AbstractUser:
    - username
    - first_name
    - last_name
    - email
    - password
    - is_active
    - is_staff
    - is_superuser
    - groups
    - user_permissions
    
    Adds custom field:
    - is_management: Boolean flag to designate institutional administrators.
    """
    
    is_management = models.BooleanField(
        default=False,
        help_text="Designates whether this user can manage the institution."
    )
    
    # Optional: Add other profile fields here later if needed
    # phone_number = models.CharField(max_length=20, blank=True, null=True)
    # address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username