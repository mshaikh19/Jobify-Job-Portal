import os

from django.core.files.storage import FileSystemStorage
from django.db import models
from django_resized import ResizedImageField

from .Address import Address
from .Certifications import Certification
from .CustomUserModel import CustomUser
from .Education import Education
from .Experience import Experience
from .SchoolAddres import SchoolAddress


class JobSeekerProfile(models.Model):
    LOCATION_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'On-site')
    ]
    GENDER_CHOICE = [
        ('female', 'Female'),
        ('male', 'Male'),
        ('other', 'Other')
    ]
    RELOCATION_CHOICES = [
        ('yes' , 'Yes'),
        ('no' , 'No')
    ]
    PROFILE_CHOICE = [
        ('public', 'Public'),
        ('private' , 'Private')
    ]
    

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='job_seeker_profile')
    
    # Part 1: Basic Info
    gender = models.CharField(max_length=50, choices=GENDER_CHOICE, null=True)
    age = models.IntegerField(null=True, blank=True)
    about = models.TextField(blank=True, null=True)
    address = models.OneToOneField(Address, on_delete=models.CASCADE , null=True)

    location_preference = models.CharField(
        max_length=10,
        choices=LOCATION_CHOICES,
        default='hybrid'
    )
    onsite_location = models.CharField(max_length=100, blank=True, null=True)

    # Part 2: Professional Details
    skills = models.CharField(max_length=500, blank=True)
    work_experience = models.PositiveIntegerField(default=0,blank=True, null=True)
    certificates = models.ManyToManyField(Certification ,blank = True)
    experiences = models.ManyToManyField(Experience, blank=True)  # Add ManyToManyField for Experience

    # Part 3: Education & Documents
    education = models.ManyToManyField(Education , blank=True , related_name="education")
    resume = models.FileField(
        upload_to='resumes/',
        blank=True,
        null=True,
        # storage=FileSystemStorage(location=os.path.join('protected', 'resumes'))
    )
    
    expected_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    desired_position = models.CharField(max_length=100, blank=True, null=True)
    relocation = models.CharField(max_length=50, choices=RELOCATION_CHOICES, null=True)
    job_type = models.CharField(max_length=500 , blank=True)
    profile_visibility = models.CharField(max_length=50 , choices=PROFILE_CHOICE , null = True)
