import datetime

from django.db import models

from job_portal.models.SchoolAddres import SchoolAddress


class Education(models.Model):
    LEVEL_CHOICES = [
        ("High School Diploma", "High School Diploma"),
        ("Associate Degree", "Associate Degree"),
        ("Bachelor's Degree" , "Bachelor's Degree") , 
        ("Master's Degree" , "Master's Degree"),
        ("Ph.D. or Doctorate" , "Ph.D. or Doctorate"),
        ("Diploma" , "Diploma"),
        ("Certificate Course", "Certificate Course"),
        ("Other" , "Other")
    ]
    ENROLLMENT_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
    ]
    FIELD_CHOICES=[
        ('Computer Science', 'Computer Science'),
        ('Information Technology', 'Information Technology'),
        ('Engineering', 'Engineering'),
        ('Business Administration', 'Business Administration'),
        ('Finance', 'Finance'),
        ('Marketing', 'Marketing'),
        ('Economics', 'Economics'),
        ('Psychology', 'Psychology'),
        ('Education', 'Education'),
        ('Biology', 'Biology'),
        ('Chemistry', 'Chemistry'),
        ('Physics', 'Physics'),
        ('Mathematics', 'Mathematics'),
        ('English Literature', 'English Literature'),
        ('Journalism', 'Journalism'),
        ('Law', 'Law'),
        ('Medicine', 'Medicine'),
        ('Nursing', 'Nursing'),
        ('Architecture', 'Architecture'),
        ('Other', 'Other'),
    ]

    current_year = datetime.date.today().year
    YEAR_CHOICES = [(year, str(year)) for year in range(1990, current_year + 1)]


    school_address = models.OneToOneField(SchoolAddress , on_delete=models.CASCADE , null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES , null=True)
    field = models.CharField(max_length=255 , null=True , choices=FIELD_CHOICES)
    currently_enrolled = models.CharField(max_length=3, choices=ENROLLMENT_CHOICES , null=True)
    start_year = models.CharField(max_length = 100 , choices=YEAR_CHOICES , null=True)
    end_year = models.CharField(max_length = 100 , choices=YEAR_CHOICES , null=True, blank=True)
    
    def __str__(self):
        return f"{self.level} in {self.field} at {self.school_name}"

