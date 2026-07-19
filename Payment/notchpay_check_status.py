#!/usr/bin/env python3
import urllib.request
import json
import ssl
import sys

# Live Credentials
PUBLIC_KEY = "pk.v0cc8AYq71qC55t3WqhRYLqYf4nRKbZJsgvnlcEBdEXFduMwc8rvLIwFuirD8SSjZ6an4xMe76jCkLgQPtit6zoZFm4TWkFhM8k5HGUpWgp1oZ9FBKj1977Hg3Dz2"
BASE_URL = "https://api.notchpay.co"

def check_payment_status(reference):
    # First try with transaction reference, then with merchant reference if that fails
    url = f"{BASE_URL}/payments/{reference}"
    
    headers = {
        "Authorization": PUBLIC_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers, method="GET")
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    print(f"Checking status for reference: {reference}...")
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            body = response.read().decode('utf-8')
            data = json.loads(body)
            
            print(f"HTTP Status: {response.getcode()}")
            
            if "transaction" in data:
                trx = data["transaction"]
                print(f"Transaction Status: {trx.get('status')}")
                print(f"Amount: {trx.get('amount')} {trx.get('currency')}")
                print(f"Reference: {trx.get('reference')}")
                print(f"NotchPay Ref: {trx.get('trxref')}")
            else:
                print(f"Response: {body}")
                
            return data
    except urllib.error.HTTPError as e:
        print(f"Error: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    # Check the status of the new 50 XAF transaction
    reference = "trx.YiA80kVK29ODlsuOTkpCukFx"
    check_payment_status(reference)
