#!/usr/bin/env python3
import urllib.request
import json
import ssl
import time

# Live Credentials from Live.key
PUBLIC_KEY = "pk.v0cc8AYq71qC55t3WqhRYLqYf4nRKbZJsgvnlcEBdEXFduMwc8rvLIwFuirD8SSjZ6an4xMe76jCkLgQPtit6zoZFm4TWkFhM8k5HGUpWgp1oZ9FBKj1977Hg3Dz2"
BASE_URL = "https://api.notchpay.co"

def check_payment_status(reference):
    url = f"{BASE_URL}/transactions/{reference}"
    
    headers = {
        "Authorization": PUBLIC_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    print(f"Checking status for reference: {reference}")
    
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

def progressive_status_check():
    # Use the reference from the payment we just initiated
    reference = "trx.eumLGVJwmUc8xIoNTrXKGoWb"  # This is the transaction reference from the successful payment
    
    print("Starting progressive status checks...")
    print("Press Ctrl+C to stop checking")
    
    # Check status immediately
    check_payment_status(reference)
    
    # Then check every 30 seconds for 10 minutes
    for i in range(20):  # 20 checks = 10 minutes with 30-second intervals
        print(f"\nWaiting 30 seconds before next check... (Check {i+1}/20)")
        time.sleep(30)
        
        print("\n" + "="*50)
        print(f"Progressive Status Check #{i+1}")
        status_data = check_payment_status(reference)
        
        if status_data and 'transaction' in status_data and status_data['transaction']['status'] in ['successful', 'failed', 'cancelled']:
            print(f"Transaction has reached final status: {status_data['transaction']['status']}")
            print("Stopping automatic checks.")
            break

if __name__ == "__main__":
    progressive_status_check()