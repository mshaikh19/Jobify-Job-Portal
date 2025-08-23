# myapp/utils/paypal.py
import paypalrestsdk
from django.conf import settings


def configure_paypal():
    paypalrestsdk.configure({
        "mode": settings.PAYPAL_MODE,  # sandbox or live
        "client_id": settings.PAYPAL_CLIENT_ID,
        "client_secret": settings.PAYPAL_CLIENT_SECRET
    })
