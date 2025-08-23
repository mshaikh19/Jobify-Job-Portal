from django.db import models


class Address(models.Model):
    street_address = models.CharField(max_length=255 , null=True)
    city = models.CharField(max_length=100 , null=True)
    state = models.CharField(max_length=100  , null=True)
    country = models.CharField(max_length=100 , null=True )