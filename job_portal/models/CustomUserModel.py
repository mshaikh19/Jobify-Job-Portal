import hashlib

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.files.storage import default_storage
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)

        if not user.profile_picture:
            user.profile_picture = self.generate_ui_avatar(email)
            
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, email, password, **extra_fields)
    
    @staticmethod
    def generate_ui_avatar(email, size=100, background="random", color="fff"):
        """Generate UI Avatar URL based on the user's email."""
        return f"https://ui-avatars.com/api/?name={email}&size={size}&background={background}&color={color}"

def user_profile_picture_path(instance, filename):
    """Generate file path for user profile pictures"""
    return f"profile_pictures/{instance.id}/{filename}"

# Custom User Model
class CustomUser(AbstractUser):
    USER_TYPES = (
        ('company', 'Company'),
        ('job_seeker', 'Job Seeker'),
        ('company_person' , 'Company Person')
    )
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    profile_picture = models.ImageField(blank=True, null=True, upload_to = user_profile_picture_path)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',
        blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        """Override save method to set profile picture if not provided."""
        if not self.profile_picture:  # Ensure no file exists before assigning UI avatar
            self.profile_picture = CustomUserManager.generate_ui_avatar(self.email)
        super().save(*args, **kwargs)

    def get_profile_picture_url(self):
        """Return profile picture URL, fallback to UI Avatar if not uploaded."""
        if self.profile_picture and hasattr(self.profile_picture, "url"):
            return self.profile_picture.url
        return CustomUserManager.generate_ui_avatar(self.email)

    def get_full_name(self):
        return f"{self.first_name}-{self.last_name}".strip()