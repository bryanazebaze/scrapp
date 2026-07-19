# NotchPay Payment and Transfer Endpoint - Working Report

## Successful Payment Transaction

### Transaction Details
- **Date**: December 20, 2025
- **Amount**: 25 XAF
- **Recipient**: +237650529088
- **Channel**: CM.MTN (Cameroon MTN Mobile Money)
- **Status**: Complete
- **Transaction ID**: trx.ToZtt3slCpAvFfNEsHIigMqJ
- **NotchPay Reference**: live_1766246410_yqla
- **Alternative Payment Link**: https://pay.notchpay.co/advDPSmEU6hxp6nUxeFlINJavHLjiaKQRy5dzTUDTruzDHFZ1O1EuQEsLQo38krneNMhK5TBEmLCXfiU3Sl0Fx0KZZq0wtx0qte8aBU80HUEuqaNIObhSpztKdh0ClGj

### Payment Request Payload
```json
{
    "amount": 25,
    "currency": "XAF",
    "phone": "+237650529088",
    "description": "User requested payment of 25 XAF",
    "reference": "trx.ToZtt3slCpAvFfNEsHIigMqJ",
    "channel": "cm.mtn"
}
```

### Authentication
- **Public Key**: pk.v0cc8AYq71qC55t3WqhRYLqYf4nRKbZJsgvnlcEBdEXFduMwc8rvLIwFuirD8SSjZ6an4xMe76jCkLgQPtit6zoZFm4TWkFhM8k5HGUpWgp1oZ9FBKj1977Hg3Dz2
- **Base URL**: https://api.notchpay.co

### Payment Flow
1. POST request to `/payments` endpoint
2. Transaction initialized with status "pending"
3. Recipient receives mobile notification
4. Recipient accepts payment on mobile device
5. Transaction status updates to "complete"

### Notes
- Previous attempts with 5 XAF remained in "pending" or "expired" status
- Higher amounts (10 XAF and 25 XAF) showed better success rates
- Small amounts may not trigger prominent notifications on recipient's device
- Payment requests remain active for approximately 15-30 minutes before expiring

## Complete Payment Request Functionality Guide

### Endpoints
- **Create Payment**: `POST /payments`
- **List Payments**: `GET /payments`
- **Get Payment**: `GET /payments/{reference}`
- **Cancel Payment**: `DELETE /payments/{reference}`

### Required Authentication
- `Authorization: <PUBLIC_KEY>` (standard auth for payments)

### Create Payment Parameters
- **amount** (required): Amount to charge in the smallest currency unit
- **currency** (required): Three-letter ISO currency code (e.g., XAF)
- **email**: Customer's email address (required if `phone` and `customer` are not provided)
- **phone**: Customer's phone number (required if `email` and `customer` are not provided)
- **customer**: Customer ID or object (required if `email` and `phone` are not provided)
- **description**: Description of the payment
- **reference**: Unique reference for the payment
- **callback**: URL to redirect after payment completion
- **locked_channel**: Restrict to a specific payment channel (e.g., 'cm.mtn', 'cm.orange')
- **locked_country**: Restrict to a specific country
- **locked_currency**: Restrict to a specific currency

### Example Payment Request
```python
import urllib.request
import json
import ssl

# Configuration
PUBLIC_KEY = "pk.v0cc8AYq71qC55t3WqhRYLqYf4nRKbZJsgvnlcEBdEXFduMwc8rvLIwFuirD8SSjZ6an4xMe76jCkLgQPtit6zoZFm4TWkFhM8k5HGUpWgp1oZ9FBKj1977Hg3Dz2"
BASE_URL = "https://api.notchpay.co"

# Create payment request
def make_payment_request(amount, phone, description, channel="cm.mtn"):
    url = f"{BASE_URL}/payments"
    
    payload = {
        "amount": amount,
        "currency": "XAF",
        "phone": phone,
        "description": description,
        "reference": f"pay_{int(time.time())}",
        "channel": channel
    }
    
    headers = {
        "Authorization": PUBLIC_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    # Create SSL context
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            body = response.read().decode('utf-8')
            return json.loads(body)
    except urllib.error.HTTPError as e:
        print(f"Error: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Exception: {str(e)}")

# Example usage
result = make_payment_request(25, "+237650529088", "Test payment of 25 XAF")
print(result)
```

### Payment Statuses
- **pending**: Payment has been initialized but not yet processed
- **processing**: Payment is being processed by the payment provider
- **complete**: Payment has been completed
- **failed**: Payment attempt failed
- **canceled**: Payment was canceled by the merchant or customer
- **expired**: Payment expired before completion

### Payment Response Structure
```json
{
  "status": "Accepted",
  "message": "Payment initialized",
  "code": 201,
  "transaction": {
    "id": "pay_123456789",
    "reference": "order_123",
    "amount": 5000,
    "currency": "XAF",
    "status": "pending",
    "customer": "cus_123456789",
    "created_at": "2023-01-01T12:00:00Z"
  },
  "authorization_url": "https://pay.notchpay.co/pay_123456789"
}
```

### Best Practices
1. Use unique references for each payment
2. Always verify payment status before fulfilling orders
3. Use webhooks for reliable payment notifications
4. Handle errors appropriately with user-friendly messages
5. Store payment references for reconciliation
6. Test with different amounts to understand recipient behavior

## Next Steps
Continue testing transfer functionality to move funds from merchant account to mobile money wallets once sufficient funds are available.