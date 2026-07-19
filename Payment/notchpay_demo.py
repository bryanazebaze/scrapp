import urllib.request
import json
import ssl
import time

# --- CONFIGURATION ---
# Load credentials from notchpay.key (assuming it's in the same directory)
# Format expected in notchpay.key:
# Public : pk_test...
# Private : sk_test...
try:
    with open('notchpay.key', 'r') as f:
        lines = f.readlines()
        PUBLIC_KEY = lines[0].strip().split(': ')[1].strip()
        PRIVATE_KEY = lines[1].strip().split(': ')[1].strip()
except FileNotFoundError:
    print("Error: 'notchpay.key' file not found.")
    exit(1)

BASE_URL = "https://api.notchpay.co"

# --- HELPER FUNCTIONS ---

def make_request(endpoint, method="GET", data=None, auth_type="standard"):
    """
    Handles API requests to Notch Pay.
    auth_type: 
      - "standard": Uses Authorization header with Public Key (for Payments).
      - "sensitive": Uses Authorization (Public) + X-Grant (Private) (for Transfers/Beneficiaries).
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
    
    # Create SSL context (ignoring certs for demo/sandbox compatibility)
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

# --- MAIN WORKFLOWS ---

def create_partner_beneficiary(name, phone_number):
    """
    Step 1: Create a beneficiary for the partner you want to split payments with.
    """
    print(f"\n[Step 1] Creating Beneficiary: {name} ({phone_number})...")
    
    payload = {
        "name": name,
        "channel": "cm.mtn", # Example: MTN Cameroon
        "number": phone_number,
        "phone": phone_number,
        "country": "CM",
        "currency": "XAF"
    }
    
    # Note: Sensitive endpoints require X-Grant header
    res, status = make_request("/beneficiaries", method="POST", data=payload, auth_type="sensitive")
    
    if status in [200, 201]:
        # Handle different response structures
        ben_id = res.get("beneficiary", {}).get("id") or res.get("id")
        print(f"SUCCESS: Created Beneficiary ID: {ben_id}")
        return ben_id
    else:
        print(f"FAILED ({status}): {res}")
        return None

def receive_payment_from_user(amount, user_email):
    """
    Step 2: Initialize a payment to receive money from a user (100% of amount).
    """
    print(f"\n[Step 2] Initializing Payment from User: {amount} XAF...")
    
    payload = {
        "amount": amount,
        "currency": "XAF",
        "email": user_email,
        "description": "Service Payment",
        "reference": f"pay_{{int(time.time())}}", # Unique reference
    }
    
    # Standard auth is sufficient for initializing payments
    res, status = make_request("/payments", method="POST", data=payload, auth_type="standard")
    
    if status in [200, 201]:
        print(f"SUCCESS: Payment Initialized.")
        print(f"Payment URL: {res.get('authorization_url')}")
        print("NOTE: In a real app, redirect user to this URL. Wait for Webhook 'payment.complete' before splitting.")
        return True
    else:
        print(f"FAILED ({status}): {res}")
        return False

def split_payment_to_partner(total_amount, partner_percent, partner_ben_id):
    """
    Step 3: Transfer the split amount (e.g., 95%) to the partner.
    Call this ONLY after confirming the user's payment is successful.
    """
    split_amount = int(total_amount * (partner_percent / 100))
    print(f"\n[Step 3] Splitting Payment: Sending {split_amount} XAF ({partner_percent}%) to Partner ({partner_ben_id})...")
    
    payload = {
        "amount": split_amount,
        "currency": "XAF",
        "channel": "cm.mtn",
        "beneficiary": partner_ben_id,
        "reference": f"split_{{int(time.time())}}",
        "description": f"Partner Split {partner_percent}%"
    }
    
    # Transfers are sensitive operations
    res, status = make_request("/transfers", method="POST", data=payload, auth_type="sensitive")
    
    if status in [200, 201]:
        print(f"SUCCESS: Transfer Initiated.")
        print(res)
    elif status == 500:
        print("FAILED (500): Internal Error. In Sandbox, this usually means 'Insufficient Funds' because the initial payment wasn't actually completed by a human.")
    elif status == 422:
        print(f"FAILED (422): Validation Error. {res}")
    else:
        print(f"FAILED ({status}): {res}")

# --- EXECUTION ---

if __name__ == "__main__":
    print("=== Notch Pay Split Payment Demo ===")
    
    # 1. Create Partner
    # Use valid test number: +237670000000 (Success), +237670000001 (Insufficient Funds), etc.
    partner_id = create_partner_beneficiary("My Partner", "+237670000000")
    
    if partner_id:
        # 2. Receive Payment (e.g., 10,000 XAF)
        # In a real app, this happens asynchronously.
        if receive_payment_from_user(10000, "user@example.com"):
            
            # 3. Split Payment (95%)
            # NOTE: This will likely fail with 500/Insufficient Funds in this script 
            # because we didn't actually go to the URL and pay.
            print("\n(...) Simulating wait for payment completion (...)")
            split_payment_to_partner(10000, 95, partner_id)
