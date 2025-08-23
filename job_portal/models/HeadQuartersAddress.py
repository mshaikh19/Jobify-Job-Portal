from django.db import models


class HeadQuartersAddress(models.Model):
    street_address = models.CharField(max_length=255 , null=True)
    city = models.CharField(max_length=100 , null=True)
    state = models.CharField(max_length=100 , null=True)
    country = models.CharField(max_length=100 , null=True)

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}, {self.country}"
