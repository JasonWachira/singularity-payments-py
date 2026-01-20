import os

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_ENVIRONMENT = "sandbox"
MPESA_CALLBACK_URL = ""

MPESA_OPTIONS = {
    "requestTimeout": 30000,
    "rateLimitOptions": {
        "enabled": True,
        "maxRequests": 100,
        "windowMs": 60000,
    }
}