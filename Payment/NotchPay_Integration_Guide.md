# Notch Pay Integration Guide: Split Payments

This guide documents how to implement a **Split Payment** flow (receive 100%, payout 95% to partner) using the Notch Pay API.

## 1. Authentication

Notch Pay has a unique authentication requirement for different endpoints.

*   **Standard Endpoints** (e.g., Initialize Payment):
    *   Header: `Authorization: <YOUR_PUBLIC_KEY>`
    *   Example: `Authorization: pk_test.zpZ...`

*   **Sensitive Endpoints** (e.g., Transfers, Beneficiaries):
    *   **Required:** You must send **BOTH** the Public Key (Authorization) and the Private Key (X-Grant).
    *   Header 1: `Authorization: <YOUR_PUBLIC_KEY>`
    *   Header 2: `X-Grant: <YOUR_PRIVATE_KEY>`

> **Note:** Your API keys are located in `notchpay.key`.

## 2. Workflow: Split Payments

Since Notch Pay does not support a native "split" parameter in the payment initialization for your specific use case, the recommended flow is **Receive -> Payout**.

### Step 1: Create Partner Beneficiary
Before you can pay a partner, you must register them as a "Beneficiary". You only need to do this once per partner.

*   **Endpoint:** `POST https://api.notchpay.co/beneficiaries`
*   **Auth:** Sensitive (Public + X-Grant)
*   **Payload:**
    ```json
    {
        "name": "Partner Name",
        "channel": "cm.mtn",  // e.g., 'cm.orange', 'cm.mtn'
        "number": "+237670000000", // Phone number (Must be international format)
        "phone": "+237670000000",
        "country": "CM",
        "currency": "XAF"
    }
    ```
*   **Success Response:** Returns a JSON object containing the `id` (e.g., `bn.test_...`). **Save this ID.**

### Step 2: Receive Payment (from User)
Initialize a payment request for the full amount (100%).

*   **Endpoint:** `POST https://api.notchpay.co/payments`
*   **Auth:** Standard (Public Key only)
*   **Payload:**
    ```json
    {
        "amount": 10000,
        "currency": "XAF",
        "email": "user@email.com",
        "description": "Service Payment",
        "reference": "your_unique_order_id"
    }
    ```
*   **Response:** Returns `authorization_url`. Redirect the user to this URL to pay.

### Step 3: Verify Payment (Webhook)
**Crucial:** Do not split funds until you confirm the user has paid.
1.  Set up a Webhook endpoint on your server.
2.  Wait for the `payment.complete` event.
3.  Verify the signature (using your Hash Key).

### Step 4: Transfer to Partner (The Split)
Once the payment is confirmed (and your Notch Pay balance is updated), initiate a transfer for 95% of the amount to the Partner's Beneficiary ID.

*   **Endpoint:** `POST https://api.notchpay.co/transfers`
*   **Auth:** Sensitive (Public + X-Grant)
*   **Payload:**
    ```json
    {
        "amount": 9500, // 95% of 10000
        "currency": "XAF",
        "channel": "cm.mtn",
        "beneficiary": "bn.test_...", // ID from Step 1
        "reference": "split_payment_ref",
        "description": "95% Partner Split"
    }
    ```

## 3. Testing in Sandbox

### Test Numbers
When creating beneficiaries or making payments in Sandbox, use these specific numbers to simulate scenarios:

*   `+237670000000`: **Success**
*   `+237670000001`: **Insufficient Funds**
*   `+237670000002`: **Failure**
*   `+237670000003`: **Timeout**
*   `+237670000004`: **Canceled**

### Common Errors
*   **401 Unauthorized:** Check your keys. Remember `X-Grant` for transfers.
*   **422 Unprocessable Entity:** Invalid phone number format. Use `+237...`.
*   **500 Internal Error (during Transfer):** In Sandbox, this often means your merchant account has **0 balance**. Since you are testing via API scripts without physically completing the payment on the `authorization_url`, your balance remains 0, so the transfer fails. This is expected behavior in scripts.

## 4. Code Example

A complete Python reference implementation is available in `notchpay_demo.py` in your directory.
