from django.contrib.auth.models import User
from django.db import models

from .Job import Job
from .JobSeeker import \
    JobSeekerProfile  # replace with your actual Job model import


class SavedJob(models.Model):
    job_seeker = models.ForeignKey(JobSeekerProfile, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('job_seeker', 'job')  # Prevent duplicate saves

    def __str__(self):
        return f"{self.job_seeker.user.username} saved {self.job.title}"
