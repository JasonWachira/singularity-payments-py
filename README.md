# Singularity Payments

A modern Python SDK for integrating M-Pesa payments into your applications. Built with developer experience in mind, featuring automatic retries, rate limiting, and comprehensive error handling.

[![PyPI version](https://img.shields.io/pypi/v/singularity-payments.svg)](https://pypi.org/project/singularity-payments/)
[![License](https://img.shields.io/pypi/l/singularity-payments.svg)](https://github.com/yourusername/singularity-payments/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

## Features

- ✅ **Easy to Use** - Simple, intuitive API that gets you up and running in minutes
- ✅ **Auto Retry** - Built-in retry logic with exponential backoff for failed requests
- ✅ **Rate Limiting** - Protect your application with configurable rate limits
- ✅ **Multiple Frameworks** - Support for Django, FastAPI, and Flask
- ✅ **Secure** - IP validation, duplicate prevention, and secure credential handling
- ✅ **Lightweight** - Minimal dependencies, optimized for performance
- ✅ **Great Documentation** - Detailed docs with real-world examples

## Supported M-Pesa APIs

- ✅ STK Push (Lipa Na M-Pesa Online)
- ✅ STK Query (STK Transaction Status)
- ✅ C2B (Customer to Business)
- ✅ B2C (Business to Customer)
- ✅ B2B (Business to Business)
- ✅ Account Balance
- ✅ Transaction Status
- ✅ Reversal
- ✅ Dynamic QR Code Generation

## Installation

```bash
# Django
pip install singularity-payments[django]

# FastAPI
pip install singularity-payments[fastapi]

# Flask
pip install singularity-payments[flask]

# Core only (no framework integration)
pip install singularity-payments
```

## Quick Start

### 1. Get M-Pesa Credentials

Sign up at [Safaricom Daraja Portal](https://developer.safaricom.co.ke/) and get the Sandbox:
- Consumer Key
- Consumer Secret

### 2. Set Up Environment Variables

```bash
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_ENVIRONMENT=sandbox
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback
```

### 3. Initialize Client

```python
from singularity_payments import MpesaClient
import os

mpesa = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL")
)
```

### 4. Initiate Payment

```python
response = mpesa.stkPush(
    amount=100,
    phone_number="254712345678",
    account_reference="INV-001",
    transaction_desc="Payment for Order #001"
)

print(response["CheckoutRequestID"])
```

### 5. Handle Callbacks

```python
def on_success(data):
    print(f"Payment successful: {data['mpesa_receipt_number']}")
    # Update your database
    Order.objects.filter(
        checkout_request_id=data["CheckoutRequestID"]
    ).update(status="paid")

def on_failure(data):
    print(f"Payment failed: {data['error_message']}")
    # Handle failure

mpesa = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL"),
    callback_options={
        "on_success": on_success,
        "on_failure": on_failure,
        "validate_ip": True
    }
)
```

## Advanced Features

### Rate Limiting

Protect your application from excessive API calls:

```python
mpesa = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL"),
    rate_limit_options={
        "enabled": True,
        "max_requests": 100,
        "window_ms": 60000
    }
)
```

### Redis-Based Rate Limiting

For distributed systems:

```python
import redis

redis_client = redis.from_url(os.getenv("REDIS_URL"))

mpesa = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL"),
    rate_limit_options={
        "enabled": True,
        "max_requests": 100,
        "window_ms": 60000,
        "redis": redis_client
    }
)
```

### Automatic Retries

Built-in retry logic with exponential backoff:

```python
mpesa = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL"),
    retry_options={
        "max_retries": 3,
        "initial_delay_ms": 1000,
        "max_delay_ms": 10000,
        "backoff_multiplier": 2
    }
)
```

### Custom Timeout

Configure request timeout:

```python
mpesa = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL"),
    request_timeout=45  # 45 seconds
)
```

### Duplicate Prevention

Prevent processing duplicate callbacks:

```python
def is_duplicate(checkout_request_id):
    return Payment.objects.filter(
        checkout_request_id=checkout_request_id
    ).exists()

mpesa = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL"),
    callback_options={
        "is_duplicate": is_duplicate
    }
)
```

## Complete Payment Flow Example

```python
from singularity_payments import MpesaClient
from myapp.models import Payment, Product
from datetime import datetime
import os

# Initialize client
def on_success(data):
    Payment.objects.filter(
        checkout_request_id=data["CheckoutRequestID"]
    ).update(
        status="completed",
        mpesa_receipt_number=data["mpesa_receipt_number"],
        transaction_date=datetime.fromisoformat(data["transaction_date"])
    )

def on_failure(data):
    Payment.objects.filter(
        checkout_request_id=data["CheckoutRequestID"]
    ).update(
        status="failed",
        error_message=data["error_message"]
    )

def is_duplicate(checkout_request_id):
    payment = Payment.objects.filter(
        checkout_request_id=checkout_request_id
    ).first()
    return payment and payment.status == "completed"

mpesa = MpesaClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL"),
    callback_options={
        "on_success": on_success,
        "on_failure": on_failure,
        "validate_ip": True,
        "is_duplicate": is_duplicate
    },
    rate_limit_options={
        "enabled": True,
        "max_requests": 100,
        "window_ms": 60000
    }
)

# Initiate payment
def initiate_payment(product_id, phone_number):
    # Get product details
    product = Product.objects.get(id=product_id)
    
    # Initiate STK Push
    response = mpesa.stkPush(
        amount=product.price,
        phone_number=phone_number,
        account_reference=f"ORDER-{product_id}",
        transaction_desc=f"Payment for {product.name}"
    )
    
    # Save payment record
    Payment.objects.create(
        checkout_request_id=response["CheckoutRequestID"],
        merchant_request_id=response["MerchantRequestID"],
        product_id=product_id,
        phone_number=phone_number,
        amount=product.price,
        status="pending"
    )
    
    return response

# Query payment status
def check_payment_status(checkout_request_id):
    status = mpesa.stk_query(checkout_request_id=checkout_request_id)
    
    if status["ResultCode"] == "0":
        print("Payment successful!")
    else:
        print(f"Payment status: {status['ResultDesc']}")
    
    return status
```

## Framework Integration

### Django

```python
# settings.py
SINGULARITY_PAYMENTS = {
    'CONSUMER_KEY': os.getenv('MPESA_CONSUMER_KEY'),
    'CONSUMER_SECRET': os.getenv('MPESA_CONSUMER_SECRET'),
    'SHORTCODE': os.getenv('MPESA_SHORTCODE'),
    'PASSKEY': os.getenv('MPESA_PASSKEY'),
    'ENVIRONMENT': 'sandbox',
    'CALLBACK_URL': os.getenv('MPESA_CALLBACK_URL'),
}

# views.py
from singularity_payments.django import MpesaDjangoClient
from django.http import JsonResponse

mpesa = MpesaDjangoClient()

def initiate_payment(request):
    response = mpesa.stkPush(
        amount=100,
        phone_number="254712345678",
        account_reference="INV-001",
        transaction_desc="Payment"
    )
    return JsonResponse(response)

# urls.py
from singularity_payments.django import stk_callback

urlpatterns = [
    path('api/mpesa/callback/', stk_callback, name='mpesa_callback'),
]
```

### FastAPI

```python
from fastapi import FastAPI, Request
from singularity_payments.fastapi import MpesaFastAPIClient, mpesa_callback_handler
import os

app = FastAPI()

mpesa = MpesaFastAPIClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL")
)

@app.post("/api/payment/initiate")
async def initiate_payment():
    response = await mpesa.stkPush(
        amount=100,
        phone_number="254712345678",
        account_reference="INV-001",
        transaction_desc="Payment"
    )
    return response

@app.post("/api/mpesa/callback")
async def callback(request: Request):
    return await mpesa_callback_handler(request, mpesa)
```

### Flask

```python
from flask import Flask, request, jsonify
from singularity_payments.flask import MpesaFlaskClient
import os

app = Flask(__name__)

mpesa = MpesaFlaskClient(
    consumer_key=os.getenv("MPESA_CONSUMER_KEY"),
    consumer_secret=os.getenv("MPESA_CONSUMER_SECRET"),
    shortcode=os.getenv("MPESA_SHORTCODE"),
    passkey=os.getenv("MPESA_PASSKEY"),
    environment="sandbox",
    callback_url=os.getenv("MPESA_CALLBACK_URL")
)

@app.route('/api/payment/initiate', methods=['POST'])
def initiate_payment():
    response = mpesa.stkPush(
        amount=100,
        phone_number="254712345678",
        account_reference="INV-001",
        transaction_desc="Payment"
    )
    return jsonify(response)

@app.route('/api/mpesa/callback', methods=['POST'])
def callback():
    return mpesa.handleStkCallback(request)
```

## Error Handling

The SDK provides specific exception classes for better error handling:

```python
from singularity_payments.exceptions import (
    MpesaValidationError,
    MpesaTimeoutError,
    MpesaNetworkError
)

try:
    response = mpesa.stkPush(
        amount=100,
        phone_number="254712345678",
        account_reference="INV-001",
        transaction_desc="Payment"
    )
except MpesaValidationError as e:
    print(f"Validation error: {e}")
except MpesaTimeoutError as e:
    print(f"Request timed out: {e}")
except MpesaNetworkError as e:
    print(f"Network error: {e}")
except Exception as e:
    print(f"Unknown error: {e}")
```

## Testing

### Sandbox Environment

Use sandbox credentials for testing:

```python
mpesa = MpesaClient(
    consumer_key="sandbox_consumer_key",
    consumer_secret="sandbox_consumer_secret",
    shortcode="174379",
    passkey="sandbox_passkey",
    environment="sandbox",
    callback_url="https://yourdomain.com/api/mpesa/callback"
)
```



## API Reference

### STK Push

```python
mpesa.stkPush(
    amount: int,
    phone_number: str,
    account_reference: str,
    transaction_desc: str,
    callback_url: str = None  # Optional override
)
```

### B2C Payment

```python
mpesa.b2c(
    amount: int,
    phone_number: str,
    command_id: str,  # "BusinessPayment", "SalaryPayment", "PromotionPayment"
    remarks: str,
    occasion: str = None,
    result_url: str = None,
    timeout_url: str = None
)
```

### B2B Payment

```python
mpesa.b2b(
    amount: int,
    party_b: str,
    command_id: str,  # "BusinessPayBill", "BusinessBuyGoods", "DisburseFundsToBusiness"
    sender_identifier_type: str,  # "1", "2", "4"
    receiver_identifier_type: str,  # "1", "2", "4"
    remarks: str,
    account_reference: str,
    result_url: str = None,
    timeout_url: str = None
)
```

## Documentation

Full documentation is available at [this link](https://payments-py.singularity.co.ke)

- [Getting Started](https://docs.singularity-payments.com/python/getting-started)
- [STK Push Guide](https://docs.singularity-payments.com/python/stk-push)
- [Rate Limiting](https://docs.singularity-payments.com/python/rate-limiting)
- [Error Handling](https://docs.singularity-payments.com/python/error-handling)
- [API Reference](https://docs.singularity-payments.com/python/api-reference)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- 📧 Email: wambua_kelvin@outlook.com
- 🐛 Issues: [GitHub Issues](https://github.com/singularity.co.ke/singularity-payments-py/issues)
- 📖 Docs: [Documentation](https://payments-py.singularity.co.ke)

## License

Apache 2.0 © [Singularity Payments](LICENSE)

## Acknowledgments

- Built on Top of [Safaricom M-Pesa](https://developer.safaricom.co.ke/)
- Inspired by the need for better payment integrations in Africa.

## Roadmap

- [ ] Comprehensive Testing for all packages (currently working on tests)
- [ ] Demo Example
- [ ] Support for more payment providers (Airtel Money, Card Payments)
- [ ] Prebuilt UI Components
- [ ] Additional Frameworks (Tornado, Pyramid, Bottle)
