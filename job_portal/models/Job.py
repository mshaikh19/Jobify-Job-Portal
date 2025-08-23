from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from job_portal.models.Company import Company
from job_portal.models.CompanyPerson import \
    CompanyPerson  # Update path based on your app structure
from job_portal.models.Location import Location


class Job(models.Model):
    JOB_TYPES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]

    WORK_LOCATION_CHOICES = [
        ('onsite', 'Onsite'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    ]
    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('hindi', 'Hindi'),
        ('spanish', 'Spanish'),
        ('french', 'French'),
        ('german', 'German'),
        ('mandarin', 'Mandarin'),
        ('tamil', 'Tamil'),
        ('telugu', 'Telugu'),
        ('bengali', 'Bengali'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    expected_start_date = models.DateField(null=True, blank=True)
    experience_required = models.CharField(max_length=100, blank=True)
    job_language = models.CharField(max_length=100, blank=True , choices=LANGUAGE_CHOICES , default='english')
    number_of_people = models.PositiveIntegerField(default=1)
    work_location_type = models.CharField(max_length=10, choices=WORK_LOCATION_CHOICES, default='onsite')
    job_location = models.OneToOneField(Location, on_delete=models.SET_NULL, null=True, blank=True)
    company_goal = models.TextField(blank=True)
    work_environment = models.TextField(blank=True)
    additional_questions = models.TextField(blank=True, help_text="Enter questions separated by new lines." , null=True)
    salary = models.PositiveIntegerField(validators=[MinValueValidator(1000)])
    requirements = models.TextField()
    application_deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    posted_by = models.ForeignKey(CompanyPerson, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_jobs')
    
    current_applicants = models.PositiveIntegerField(default=0)  # Current applicants for the job

    def is_full(self):
        return self.current_applicants >= self.number_of_people
    

    def __str__(self):  
        return f"{self.title} at {self.company.name}" 
      
    def set_requirements(self, req_list):
        self.requirements = ",".join(req_list)

    def get_requirements(self):
        return self.requirements.split(",")
    
    def get_additional_questions(self):
        return self.additional_questions.splitlines()
