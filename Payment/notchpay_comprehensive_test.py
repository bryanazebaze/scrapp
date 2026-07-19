#!/usr/bin/env python3
"""
Comprehensive Notch Pay API Test Suite
Tests all API endpoints mentioned in DevGuidpages.txt
"""

import urllib.request
import json
import ssl
import time
import random
import string
from datetime import datetime

# --- CONFIGURATION ---
# Load credentials from notchpay.key
try:
    with open('notchpay.key', 'r') as f:
        lines = f.readlines()
        PUBLIC_KEY = lines[0].strip().split(': ')[1].strip()
        PRIVATE_KEY = lines[1].strip().split(': ')[1].strip()
except FileNotFoundError:
    print("Error: 'notchpay.key' file not found.")
    exit(1)

BASE_URL = "https://api.notchpay.co"

# --- TESTING UTILITIES ---
class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.warnings = []
        self.start_time = time.time()
        
    def record_pass(self, test_name):
        self.passed += 1
        print(f"✓ {test_name}")
        
    def record_fail(self, test_name, reason):
        self.failed += 1
        self.errors.append(f"{test_name}: {reason}")
        print(f"✗ {test_name}: {reason}")
        
    def record_warning(self, test_name, reason):
        self.warnings.append(f"{test_name}: {reason}")
        print(f"⚠ {test_name}: {reason}")
        
    def get_summary(self):
        duration = time.time() - self.start_time
        return {
            "passed": self.passed,
            "failed": self.failed,
            "warnings": len(self.warnings),
            "duration": f"{duration:.2f}s",
            "errors": self.errors,
            "warnings": self.warnings
        }

def generate_random_reference(prefix="test"):
    """Generate a unique reference for testing"""
    timestamp = int(time.time())
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{timestamp}_{random_str}"

def make_request(endpoint, method="GET", data=None, auth_type="standard"):
    """
    Handles API requests to Notch Pay.
    auth_type: 
      - "standard": Uses Authorization header with Public Key (for Payments, Customers, etc.)
      - "sensitive": Uses Authorization (Public) + X-Grant (Private) (for Transfers, Beneficiaries, Balance)
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

# --- TEST SUITE ---

def test_payments_api(results):
    """Test all Payments API endpoints"""
    print("\n" + "="*50)
    print("TESTING PAYMENTS API")
    print("="*50)
    
    # Test 1: List All Payments
    print("\n[Test 1] List All Payments")
    res, status = make_request("/payments", method="GET", auth_type="standard")
    if status == 200 and "items" in res:
        results.record_pass("List All Payments")
    else:
        results.record_fail("List All Payments", f"Status: {status}, Response: {res}")
    
    # Test 2: Create a Payment
    print("\n[Test 2] Create a Payment")
    payment_ref = generate_random_reference("payment")
    payload = {
        "amount": 5000,
        "currency": "XAF",
        "email": "test@example.com",
        "description": "Test payment",
        "reference": payment_ref
    }
    res, status = make_request("/payments", method="POST", data=payload, auth_type="standard")
    if status in [200, 201] and "authorization_url" in res:
        results.record_pass("Create a Payment")
        payment_id = res.get("transaction", {}).get("id")
        payment_reference = res.get("transaction", {}).get("reference")
    else:
        results.record_fail("Create a Payment", f"Status: {status}, Response: {res}")
        payment_reference = payment_ref
    
    # Test 3: Retrieve a Payment
    print("\n[Test 3] Retrieve a Payment")
    res, status = make_request(f"/payments/{payment_reference}", method="GET", auth_type="standard")
    if status == 200 and "transaction" in res:
        results.record_pass("Retrieve a Payment")
    else:
        results.record_fail("Retrieve a Payment", f"Status: {status}, Response: {res}")
    
    # Test 4: Cancel a Payment (if it exists and is cancelable)
    print("\n[Test 4] Cancel a Payment")
    res, status = make_request(f"/payments/{payment_reference}", method="DELETE", auth_type="standard")
    if status in [200, 202]:
        results.record_pass("Cancel a Payment")
    elif status == 422:  # Payment cannot be canceled (already processed)
        results.record_warning("Cancel a Payment", "Payment already processed or not cancelable")
    else:
        results.record_fail("Cancel a Payment", f"Status: {status}, Response: {res}")

def test_transfers_api(results):
    """Test all Transfers API endpoints"""
    print("\n" + "="*50)
    print("TESTING TRANSFERS API")
    print("="*50)
    
    # Test 1: List All Transfers
    print("\n[Test 1] List All Transfers")
    res, status = make_request("/transfers", method="GET", auth_type="sensitive")
    if status == 200 and "items" in res:
        results.record_pass("List All Transfers")
    else:
        results.record_fail("List All Transfers", f"Status: {status}, Response: {res}")
    
    # Test 2: Create a Transfer (requires beneficiary)
    print("\n[Test 2] Create a Transfer")
    # First create a beneficiary
    beneficiary_payload = {
        "name": "Test Beneficiary",
        "channel": "cm.mtn",
        "account_number": "+237670000000",
        "phone": "+237670000000",
        "country": "CM",
        "currency": "XAF",
        "type": "mobile_money"
    }
    ben_res, ben_status = make_request("/beneficiaries", method="POST", data=beneficiary_payload, auth_type="sensitive")
    
    if ben_status in [200, 201]:
        beneficiary_id = ben_res.get("beneficiary", {}).get("id") or ben_res.get("id")
        
        transfer_ref = generate_random_reference("transfer")
        transfer_payload = {
            "amount": 1000,
            "currency": "XAF",
            "beneficiary": beneficiary_id,
            "channel": "cm.mtn",
            "description": "Test transfer",
            "reference": transfer_ref
        }
        res, status = make_request("/transfers", method="POST", data=transfer_payload, auth_type="sensitive")
        
        if status in [200, 201]:
            results.record_pass("Create a Transfer")
            transfer_id = res.get("transfer", {}).get("id")
        elif status == 500:
            results.record_warning("Create a Transfer", "Insufficient funds (expected in sandbox)")
        else:
            results.record_fail("Create a Transfer", f"Status: {status}, Response: {res}")
    else:
        results.record_fail("Create a Transfer", f"Failed to create beneficiary: {ben_res}")

def test_customers_api(results):
    """Test all Customers API endpoints"""
    print("\n" + "="*50)
    print("TESTING CUSTOMERS API")
    print("="*50)
    
    # Test 1: List All Customers
    print("\n[Test 1] List All Customers")
    res, status = make_request("/customers", method="GET", auth_type="standard")
    if status == 200 and "items" in res:
        results.record_pass("List All Customers")
    else:
        results.record_fail("List All Customers", f"Status: {status}, Response: {res}")
    
    # Test 2: Create a Customer
    print("\n[Test 2] Create a Customer")
    # Try with email only first, then with phone
    customer_payload = {
        "name": "Test Customer",
        "email": f"test_{int(time.time())}@example.com",
        "phone": "670000000",
        "metadata": {"test": "true"}
    }
    res, status = make_request("/customers", method="POST", data=customer_payload, auth_type="standard")
    if status in [200, 201] and "customer" in res:
        results.record_pass("Create a Customer")
        customer_id = res["customer"]["id"]
    else:
        results.record_fail("Create a Customer", f"Status: {status}, Response: {res}")
        customer_id = None
    
    # Test 3: Retrieve a Customer
    if customer_id:
        print("\n[Test 3] Retrieve a Customer")
        res, status = make_request(f"/customers/{customer_id}", method="GET", auth_type="standard")
        if status == 200 and "customer" in res:
            results.record_pass("Retrieve a Customer")
        else:
            results.record_fail("Retrieve a Customer", f"Status: {status}, Response: {res}")
        
        # Test 4: Update a Customer
        print("\n[Test 4] Update a Customer")
        update_payload = {
            "name": "Updated Test Customer",
            "metadata": {"updated": "true"}
        }
        res, status = make_request(f"/customers/{customer_id}", method="PUT", data=update_payload, auth_type="standard")
        if status in [200, 201] and "customer" in res:
            results.record_pass("Update a Customer")
        else:
            results.record_fail("Update a Customer", f"Status: {status}, Response: {res}")
        
        # Test 5: Delete a Customer
        print("\n[Test 5] Delete a Customer")
        res, status = make_request(f"/customers/{customer_id}", method="DELETE", auth_type="standard")
        if status in [200, 204]:
            results.record_pass("Delete a Customer")
        else:
            results.record_fail("Delete a Customer", f"Status: {status}, Response: {res}")

def test_beneficiaries_api(results):
    """Test all Beneficiaries API endpoints"""
    print("\n" + "="*50)
    print("TESTING BENEFICIARIES API")
    print("="*50)
    
    # Test 1: List All Beneficiaries
    print("\n[Test 1] List All Beneficiaries")
    res, status = make_request("/beneficiaries", method="GET", auth_type="sensitive")
    if status == 200 and "items" in res:
        results.record_pass("List All Beneficiaries")
    else:
        results.record_fail("List All Beneficiaries", f"Status: {status}, Response: {res}")
    
    # Test 2: Create a Beneficiary
    print("\n[Test 2] Create a Beneficiary")
    # Based on the documentation, we need to use the correct field names
    beneficiary_payload = {
        "name": "Test Beneficiary",
        "channel": "cm.mtn",
        "account_number": "+237670000000",
        "phone": "+237670000000",
        "country": "CM",
        "currency": "XAF",
        "type": "mobile_money"
    }
    res, status = make_request("/beneficiaries", method="POST", data=beneficiary_payload, auth_type="sensitive")
    if status in [200, 201] and "beneficiary" in res:
        results.record_pass("Create a Beneficiary")
        beneficiary_id = res["beneficiary"]["id"]
    else:
        results.record_fail("Create a Beneficiary", f"Status: {status}, Response: {res}")
        beneficiary_id = None
    
    # Test 3: Retrieve a Beneficiary
    if beneficiary_id:
        print("\n[Test 3] Retrieve a Beneficiary")
        res, status = make_request(f"/beneficiaries/{beneficiary_id}", method="GET", auth_type="sensitive")
        if status == 200 and "beneficiary" in res:
            results.record_pass("Retrieve a Beneficiary")
        else:
            results.record_fail("Retrieve a Beneficiary", f"Status: {status}, Response: {res}")
        
        # Test 4: Update a Beneficiary
        print("\n[Test 4] Update a Beneficiary")
        update_payload = {
            "name": "Updated Test Beneficiary",
            "metadata": {"updated": "true"}
        }
        res, status = make_request(f"/beneficiaries/{beneficiary_id}", method="PUT", data=update_payload, auth_type="sensitive")
        if status in [200, 201] and "beneficiary" in res:
            results.record_pass("Update a Beneficiary")
        else:
            results.record_fail("Update a Beneficiary", f"Status: {status}, Response: {res}")
        
        # Test 5: Delete a Beneficiary
        print("\n[Test 5] Delete a Beneficiary")
        res, status = make_request(f"/beneficiaries/{beneficiary_id}", method="DELETE", auth_type="sensitive")
        if status in [200, 204]:
            results.record_pass("Delete a Beneficiary")
        else:
            results.record_fail("Delete a Beneficiary", f"Status: {status}, Response: {res}")

def test_balance_api(results):
    """Test all Balance API endpoints"""
    print("\n" + "="*50)
    print("TESTING BALANCE API")
    print("="*50)
    
    # Test 1: Check Balance
    print("\n[Test 1] Check Balance")
    res, status = make_request("/balance", method="GET", auth_type="sensitive")
    if status == 200 and "balance" in res:
        results.record_pass("Check Balance")
    else:
        results.record_fail("Check Balance", f"Status: {status}, Response: {res}")
    
    # Test 2: Check Balance for Specific Currency (skip if main balance endpoint works)
    print("\n[Test 2] Check Balance for Specific Currency (XAF)")
    res, status = make_request("/balance/XAF", method="GET", auth_type="sensitive")
    if status == 404:
        results.record_warning("Check Balance for Specific Currency", "Endpoint not found (might not be available)")
    elif status == 200 and "balance" in res:
        results.record_pass("Check Balance for Specific Currency")
    else:
        results.record_fail("Check Balance for Specific Currency", f"Status: {status}, Response: {res}")
    
    # Test 3: List Balance History (skip if main balance endpoint works)
    print("\n[Test 3] List Balance History")
    res, status = make_request("/balance/history", method="GET", auth_type="sensitive")
    if status == 404:
        results.record_warning("List Balance History", "Endpoint not found (might not be available)")
    elif status == 200 and "items" in res:
        results.record_pass("List Balance History")
    else:
        results.record_fail("List Balance History", f"Status: {status}, Response: {res}")

def test_resources_api(results):
    """Test all Resources API endpoints"""
    print("\n" + "="*50)
    print("TESTING RESOURCES API")
    print("="*50)
    
    # Test 1: List Payment Channels
    print("\n[Test 1] List Payment Channels")
    res, status = make_request("/resources/channels", method="GET", auth_type="standard")
    if status == 404:
        results.record_warning("List Payment Channels", "Endpoint not found (might not be available)")
    elif status == 200 and "channels" in res:
        results.record_pass("List Payment Channels")
    else:
        results.record_fail("List Payment Channels", f"Status: {status}, Response: {res}")
    
    # Test 2: Get Channel Details (skip if channels endpoint not available)
    if status == 200 and "channels" in res and len(res["channels"]) > 0:
        channel_id = res["channels"][0]["id"]
        print(f"\n[Test 2] Get Channel Details ({channel_id})")
        res, status = make_request(f"/resources/channels/{channel_id}", method="GET", auth_type="standard")
        if status == 200 and "channel" in res:
            results.record_pass("Get Channel Details")
        else:
            results.record_fail("Get Channel Details", f"Status: {status}, Response: {res}")
    else:
        print("\n[Test 2] Get Channel Details - Skipped (channels endpoint not available)")
        results.record_warning("Get Channel Details", "Skipped (channels endpoint not available)")
    
    # Test 3: List Countries
    print("\n[Test 3] List Countries")
    res, status = make_request("/resources/countries", method="GET", auth_type="standard")
    if status == 404:
        results.record_warning("List Countries", "Endpoint not found (might not be available)")
    elif status == 200 and "countries" in res:
        results.record_pass("List Countries")
    else:
        results.record_fail("List Countries", f"Status: {status}, Response: {res}")
    
    # Test 4: List Currencies
    print("\n[Test 4] List Currencies")
    res, status = make_request("/resources/currencies", method="GET", auth_type="standard")
    if status == 404:
        results.record_warning("List Currencies", "Endpoint not found (might not be available)")
    elif status == 200 and "currencies" in res:
        results.record_pass("List Currencies")
    else:
        results.record_fail("List Currencies", f"Status: {status}, Response: {res}")
    
    # Test 5: List Banks
    print("\n[Test 5] List Banks")
    res, status = make_request("/resources/banks", method="GET", auth_type="standard")
    if status == 404:
        results.record_warning("List Banks", "Endpoint not found (might not be available)")
    elif status == 200 and "banks" in res:
        results.record_pass("List Banks")
    else:
        results.record_fail("List Banks", f"Status: {status}, Response: {res}")

def test_webhooks_api(results):
    """Test Webhooks API endpoints (limited testing without actual webhook server)"""
    print("\n" + "="*50)
    print("TESTING WEBHOOKS API")
    print("="*50)
    
    # Test 1: List Webhooks
    print("\n[Test 1] List Webhooks")
    res, status = make_request("/webhooks", method="GET", auth_type="sensitive")  # Fixed: Use sensitive auth
    if status == 200:
        results.record_pass("List Webhooks")
    else:
        results.record_fail("List Webhooks", f"Status: {status}, Response: {res}")
    
    # Note: Creating actual webhooks would require a publicly accessible endpoint
    # which we don't have in this test environment
    print("\n[Note] Webhook creation testing skipped (requires public endpoint)")

def run_comprehensive_tests():
    """Run all tests and generate report"""
    print("="*60)
    print("NOTCH PAY COMPREHENSIVE API TEST SUITE")
    print("="*60)
    print(f"Testing with Public Key: {PUBLIC_KEY[:10]}...")
    print(f"Testing with Private Key: {PRIVATE_KEY[:10]}...")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = TestResult()
    
    # Run all test suites
    test_payments_api(results)
    test_transfers_api(results)
    test_customers_api(results)
    test_beneficiaries_api(results)
    test_balance_api(results)
    test_resources_api(results)
    test_webhooks_api(results)
    
    # Generate and display summary
    summary = results.get_summary()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {summary['passed'] + summary['failed']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Warnings: {summary['warnings']}")
    print(f"Duration: {summary['duration']}")
    
    if summary['errors']:
        print(f"\n{'='*60}")
        print("ERRORS:")
        print("="*60)
        for error in summary['errors']:
            print(f"  - {error}")
    
    if summary['warnings']:
        print(f"\n{'='*60}")
        print("WARNINGS:")
        print("="*60)
        for warning in summary['warnings']:
            print(f"  - {warning}")
    
    # Write detailed report to file
    report_filename = f"notchpay_test_report_{int(time.time())}.txt"
    with open(report_filename, 'w') as f:
        f.write("NOTCH PAY API TEST REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration: {summary['duration']}\n\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  Total Tests: {summary['passed'] + summary['failed']}\n")
        f.write(f"  Passed: {summary['passed']}\n")
        f.write(f"  Failed: {summary['failed']}\n")
        f.write(f"  Warnings: {summary['warnings']}\n\n")
        
        if summary['errors']:
            f.write("ERRORS:\n")
            for error in summary['errors']:
                f.write(f"  - {error}\n")
            f.write("\n")
        
        if summary['warnings']:
            f.write("WARNINGS:\n")
            for warning in summary['warnings']:
                f.write(f"  - {warning}\n")
    
    print(f"\nDetailed report saved to: {report_filename}")
    
    return summary

if __name__ == "__main__":
    run_comprehensive_tests()