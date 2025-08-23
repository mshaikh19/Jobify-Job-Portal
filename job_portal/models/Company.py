import datetime
import hashlib

from django import forms
from django.core.validators import MinValueValidator
from django.db import models

from .CustomUserModel import CustomUser
from .HeadQuartersAddress import HeadQuartersAddress
from .Location import Location


class Company(models.Model):
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="company", null=True)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100, default="Technology", 
    choices=[
        ("Technology", "Technology"),
        ("Healthcare", "Healthcare"),
        ("Finance", "Finance"),
        ("Education", "Education"),
        ("Manufacturing", "Manufacturing"),
        ("Other", "Other"),
    ])
    headquarters_address = models.ForeignKey(HeadQuartersAddress, on_delete=models.CASCADE)

    founded = models.PositiveIntegerField(validators=[MinValueValidator(1900)], default=datetime.date.today().year)
    company_size = models.CharField(max_length=50, choices=[
        ("1-10", "1-10"),
        ("11-50", "11-50"),
        ("51-200", "51-200"),
        ("201-500", "201-500"),
        ("500+", "500+"),
    ], default="small")

    linkedin_profile = models.URLField(blank=True)
    company_locations = models.ManyToManyField(Location, blank=True)
    tagline = models.CharField(max_length=255, blank=True)
    registration_number = models.CharField(max_length=255 ,null=True)
    business_license = models.FileField(upload_to="business_licenses/", blank=True, null=True)
    company_policy_link = models.URLField(blank=True)


    def __str__(self):
        return self.name
    
    