#!/usr/bin/env python3
import urllib.request
import json
import ssl
import time
import random
import string

# Live Credentials from Live.key
PUBLIC_KEY = "pk.v0cc8AYq71qC55t3WqhRYLqYf4nRKbZJsgvnlcEBdEXFduMwc8rvLIwFuirD8SSjZ6an4xMe76jCkLgQPtit6zoZFm4TWkFhM8k5HGUpWgp1oZ9FBKj1977Hg3Dz2"
BASE_URL = "https://api.notchpay.co"

def generate_reference():
    return f"live_{int(time.time())}_{''.join(random.choices(string.ascii_lowercase, k=4))}"

def make_payment_request():
    url = f"{BASE_URL}/payments"
    
    # User requested: 25 XAF to 650529088 (MTN)
    payload = {
        "amount": 25,
        "currency": "XAF",
        "phone": "+237650529088",
        "description": "User requested payment of 25 XAF",
        "reference": generate_reference(),
        "channel": "cm.mtn"
    }
    
    headers = {
        "Authorization": PUBLIC_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    print(f"Sending payment request of {payload['amount']} {payload['currency']} to {payload['phone']}...")
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            body = response.read().decode('utf-8')
            print(f"Status: {response.getcode()}")
            print(f"Response: {body}")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        print(f"Error: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    make_payment_request()
