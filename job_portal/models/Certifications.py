from django.db import models


class Certification(models.Model):
    name = models.CharField(max_length=255)
    certificate_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    
    def __str__(self):
        return self.name