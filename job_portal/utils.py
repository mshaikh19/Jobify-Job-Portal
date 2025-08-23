import random

from django.conf import settings
from django.core.cache import cache
from twilio.rest import Client


def send_otp_to_phone(phone_number):
    # Generate a random 6-digit OTP
    otp = random.randint(100000, 999999)

    # Store the OTP in cache with a timeout (e.g., 5 minutes)
    cache.set(f"otp_{phone_number}", otp, timeout=300)

    # Twilio configuration (assuming you have your Twilio credentials set in settings.py)
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    # Send OTP via SMS (make sure you have a valid Twilio number)
    try:
        message = client.messages.create(
            body=f"Your OTP code is {otp}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        return {"success": True, "message": "OTP sent successfully."}
    except Exception as e:
        return {"success": False, "message": f"Failed to send OTP: {str(e)}"}
