from django.db import models


class Experience(models.Model):
    position = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    start_date = models.PositiveIntegerField()
    end_date = models.PositiveIntegerField(null=True, blank=True)  # End date can be optional
    description = models.TextField()

    def __str__(self):
        return f"{self.position} at {self.company}"
