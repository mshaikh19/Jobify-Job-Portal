from django.db import models

from job_portal.models import Job


class JobPayment(models.Model):

    STATUS_CHOICES = (
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='payments')
    payment_id = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=50 , choices=STATUS_CHOICES)
    payer_id = models.CharField(max_length=100, blank=True, null=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_currency = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"Payment {self.payment_id} for Job {self.job.id}"
