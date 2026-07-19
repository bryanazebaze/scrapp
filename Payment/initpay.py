#!/usr/bin/env python3
import urllib.request
import json
import ssl
import time
import random
import string
import sys

# Live Credentials
PUBLIC_KEY = "pk.v0cc8AYq71qC55t3WqhRYLqYf4nRKbZJsgvnlcEBdEXFduMwc8rvLIwFuirD8SSjZ6an4xMe76jCkLgQPtit6zoZFm4TWkFhM8k5HGUpWgp1oZ9FBKj1977Hg3Dz2"
BASE_URL = "https://api.notchpay.co"
PHONE_NUMBER = "+237652959183"

def generate_reference():
    return f"order_{int(time.time())}_{''.join(random.choices(string.ascii_lowercase, k=4))}"

def get_ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def initialize_payment():
    url = f"{BASE_URL}/payments"
    
    payload = {
        "amount": 10,
        "currency": "XAF",
        "customer": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": PHONE_NUMBER
        },
        "description": "Payment for Order #123",
        "reference": generate_reference(),
        "callback": "https://your-website.com/callback"
    }
    
    headers = {
        "Authorization": PUBLIC_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    print(f"--- Step 1: Initializing Payment ({payload['amount']} {payload['currency']}) ---")
    
    try:
        with urllib.request.urlopen(req, context=get_ssl_context()) as response:
            body = response.read().decode('utf-8')
            response_json = json.loads(body)
            
            if response.getcode() in [200, 201]:
                print(f"Success! Status: {response.getcode()}")
                if 'transaction' in response_json:
                    ref = response_json['transaction'].get('reference')
                    print(f"Transaction Reference: {ref}")
                    return ref
            else:
                print(f"Failed to initialize. Status: {response.getcode()}")
                print(body)
                return None
            
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
        return None
    except Exception as e:
        print(f"Exception: {str(e)}")
        return None

def trigger_payment_prompt(payment_reference):
    url = f"{BASE_URL}/payments/{payment_reference}"
    
    # Payload to trigger the prompt (e.g., MTN Mobile Money)
    payload = {
        "channel": "cm.mtn",
        "data": {
            "phone": PHONE_NUMBER
        }
    }
    
    headers = {
        "Authorization": PUBLIC_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    data = json.dumps(payload).encode('utf-8')
    # Using PUT as it is standard for updating/completing a transaction in NotchPay
    req = urllib.request.Request(url, data=data, headers=headers, method="PUT") 
    
    print(f"\n--- Step 2: Triggering Payment Prompt on {PHONE_NUMBER} ---")
    
    try:
        with urllib.request.urlopen(req, context=get_ssl_context()) as response:
            body = response.read().decode('utf-8')
            print(f"Status: {response.getcode()}")
            response_json = json.loads(body)
            print(f"Response: {json.dumps(response_json, indent=2)}")
            return response_json
            
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def check_payment_status(reference):
    url = f"{BASE_URL}/payments/{reference}"
    
    headers = {
        "Authorization": PUBLIC_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    try:
        with urllib.request.urlopen(req, context=get_ssl_context()) as response:
            body = response.read().decode('utf-8')
            return json.loads(body)
    except Exception as e:
        print(f"Error checking status: {str(e)}")
        return None

def monitor_transaction(reference):
    print(f"\n--- Step 3: Monitoring Transaction Status for {reference} ---")
    print("Checking every 5 seconds... (Press Ctrl+C to stop)")
    
    final_states = ['complete', 'failed', 'canceled', 'expired', 'rejected']
    
    while True:
        data = check_payment_status(reference)
        
        if data and "transaction" in data:
            status = data["transaction"].get("status")
            print(f"Current Status: {status}")
            
            if status in final_states:
                print(f"\nTransaction Finished. Final Status: {status.upper()}")
                break
        else:
            print("Could not retrieve status.")
        
        time.sleep(5)

if __name__ == "__main__":
    # Run Step 1
    trx_ref = initialize_payment()
    
    # If Step 1 valid, Run Step 2
    if trx_ref:
        # Small delay to ensure backend propagation if necessary
        time.sleep(1)
        trigger_result = trigger_payment_prompt(trx_ref)
        
        # If Step 2 valid (or if we just want to monitor anyway), Run Step 3
        if trigger_result:
             monitor_transaction(trx_ref)
