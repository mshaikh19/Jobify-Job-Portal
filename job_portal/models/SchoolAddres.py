from django.db import models


class SchoolAddress(models.Model):
    school_name = models.CharField(max_length=255)
    school_city = models.CharField(max_length=100)
    school_state = models.CharField(max_length=100)
    school_country = models.CharField(max_length=100)