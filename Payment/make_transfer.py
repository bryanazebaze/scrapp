#!/usr/bin/env python3
"""
Script to first receive payment then make a transfer
"""

import urllib.request
import json
import ssl
import time
import random
import string

# Load credentials from Live.key
try:
    with open('Live.key', 'r') as f:
        content = f.read()
        # Extract public key
        public_line = [line for line in content.split('\n') if 'Public' in line][0]
        PRIVATE_KEY = [line for line in content.split('\n') if 'Private:' in line][0].split('Private:')[1].strip()
        PUBLIC_KEY = public_line.split('Public :')[1].strip()
except FileNotFoundError:
    print("Error: 'Live.key' file not found.")
    exit(1)

BASE_URL = "https://api.notchpay.co"

def make_request(endpoint, method="GET", data=None, auth_type="standard"):
    """
    Handles API requests to Notch Pay.
    auth_type:
      - "standard": Uses Authorization header with Public Key
      - "sensitive": Uses Authorization (Public) + X-Grant (Private)
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # AUTHENTICATION LOGIC
    if auth_type == "standard":
        headers["Authorization"] = PUBLIC_KEY
    elif auth_type == "sensitive":
        headers["Authorization"] = PUBLIC_KEY
        headers["X-Grant"] = PRIVATE_KEY

    if data:
        encoded_data = json.dumps(data).encode('utf-8')
    else:
        encoded_data = None

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)

    # Create SSL context
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            return json.loads(response.read().decode('utf-8')), response.getcode()
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            return json.loads(body), e.code
        except:
            return {"error": body}, e.code
    except Exception as e:
        return {"error": str(e)}, 0

def make_payment_request():
    """Make a payment request to add funds to our account"""
    print("Making payment request to add funds to account...")
    
    payload = {
        "amount": 500,
        "currency": "XAF",
        "phone": "+237650529088",  # The same number we used before
        "description": "Adding funds for transfer test",
        "reference": f"pay_{int(time.time())}_{random.randint(1000, 9999)}",
        "channel": "cm.mtn"
    }
    
    res, status = make_request("/payments", method="POST", data=payload, auth_type="standard")
    
    if status in [200, 201] and "transaction" in res:
        payment_id = res["transaction"].get("id") or res["transaction"].get("reference")
        payment_status = res["transaction"]["status"]
        print(f"Payment request created successfully!")
        print(f"Payment ID/Reference: {payment_id}")
        print(f"Payment Status: {payment_status}")
        print(f"Amount: {res['transaction']['amount']} {res['transaction']['currency']}")
        if 'authorization_url' in res:
            print(f"Authorization URL: {res['authorization_url']}")
        return payment_id
    else:
        print(f"Failed to create payment request: Status {status}, Response: {res}")
        return None

def check_balance():
    """Check the account balance"""
    print("Checking account balance...")
    
    res, status = make_request("/balance", method="GET", auth_type="sensitive")
    
    if status == 200:
        print(f"Balance: {res}")
        return res
    else:
        print(f"Failed to check balance: Status {status}, Response: {res}")
        return None

def make_transfer_with_test_number():
    """Make a transfer using a test number"""
    print("Making transfer with test number +237670000000 (should succeed in sandbox)...")
    
    payload = {
        "amount": 100,  # Reduced amount to be sure we have funds
        "currency": "XAF",
        "beneficiary_data": {
            "name": "Test Beneficiary",
            "phone": "+237670000000",  # Success test number
            "email": f"test{int(time.time())}@example.com",
            "country": "CM",
            "currency": "XAF",
            "type": "mobile_money"
        },
        "channel": "cm.mtn",
        "description": "Test transfer after checking balance",
        "reference": f"transfer_{int(time.time())}_{random.randint(1000, 9999)}"
    }
    
    res, status = make_request("/transfers", method="POST", data=payload, auth_type="sensitive")
    
    if status in [200, 201] and "transfer" in res:
        transfer_id = res["transfer"]["id"]
        transfer_status = res["transfer"]["status"]
        print(f"Transfer initiated successfully!")
        print(f"Transfer ID: {transfer_id}")
        print(f"Transfer Status: {transfer_status}")
        print(f"Amount: {res['transfer']['amount']} {res['transfer']['currency']}")
        return transfer_id
    elif status == 500:
        print(f"Transfer failed: Insufficient funds or server error")
        print(f"Response: {res}")
        return None
    elif status == 503:
        print(f"Service unavailable: {res}")
        return None
    else:
        print(f"Transfer response: Status {status}, Response: {res}")
        return None

if __name__ == "__main__":
    print("=== Notch Pay Flow Test: Payment then Transfer ===")
    print(f"Public Key: {PUBLIC_KEY[:15]}...")
    print(f"Private Key: {PRIVATE_KEY[:15]}...")
    print("")

    # Check initial balance
    print("--- Checking initial balance ---")
    balance = check_balance()
    
    # Try to make a transfer (since we know there's some balance)
    print("\n--- Attempting transfer ---")
    transfer_id = make_transfer_with_test_number()
    
    if transfer_id:
        # Check the status of the transfer
        time.sleep(2)  # Wait a bit before checking status
        res, status = make_request(f"/transfers/{transfer_id}", method="GET", auth_type="sensitive")
        
        if status == 200 and "transfer" in res:
            transfer = res["transfer"]
            print(f"Final Transfer Status: {transfer['status']}")
            print(f"Amount: {transfer['amount']} {transfer['currency']}")
            print(f"Description: {transfer['description']}")
        
        print("\nTransfer test completed successfully.")
    else:
        print("Transfer test failed.")
        
        # If transfer failed due to low balance, try to create a payment request
        if balance and balance.get('balance', {}).get('available', 0) < 500:
            print("\n--- Balance may be too low, creating payment request ---")
            payment_id = make_payment_request()
            if payment_id:
                print("Payment request created. Funds will be added to your account when the recipient pays.")
                # Show updated balance after a while
                print("After the payment is completed by the recipient, your balance will be updated, and you can try transfers again.")