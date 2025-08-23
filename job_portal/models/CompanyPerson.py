from django.db import models

from .Company import Company
from .CustomUserModel import CustomUser


class CompanyPerson(models.Model):
    POSITION_CHOICES = [
        ('CEO', 'Chief Executive Officer'),
        ('CTO', 'Chief Technology Officer'),
        ('CFO', 'Chief Financial Officer'),
        ('HR', 'Human Resources'),
        ('ENG', 'Engineer'),
        ('MKT', 'Marketing'),
        ('SALES', 'Sales'),
        ('OTHER', 'Other'),
    ]
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='persons' , null=True)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE , null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    position = models.CharField(max_length=255 , choices=POSITION_CHOICES, null=True)
    is_admin = models.BooleanField(default=False , null=True)