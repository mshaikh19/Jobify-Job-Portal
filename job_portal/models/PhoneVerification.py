
from django.db import models

from job_portal.models.CustomUserModel import CustomUser


class PhoneVerification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Phone Verification"
        verbose_name_plural = "Phone Verifications"

    def __str__(self):
        return f"OTP for {self.phone_number}"