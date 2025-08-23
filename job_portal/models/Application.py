from django.db import models

from .Job import Job
from .JobSeeker import JobSeekerProfile


class Application(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE , null=True , related_name="applications")
    job_seeker = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE , null=True)
    cover_letter = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='application_resumes/' , null=True)
    custom_answers = models.JSONField(blank=True, null=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('review', 'In Review'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),

    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    applied_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('job_seeker', 'job')
    def __str__(self):
        return f"{self.job_seeker.user.get_full_name()} - {self.job.title}"