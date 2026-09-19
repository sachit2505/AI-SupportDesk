# Sample Support Knowledge Base

## 1. Password Reset & Account Lockout
If a user is locked out of their account due to multiple failed login attempts:
1. Navigate to the login screen and select "Forgot Password".
2. Enter the registered email address.
3. Check the inbox for a 6-digit verification code (valid for 15 minutes).
4. If the code does not arrive within 5 minutes, verify the spam folder.
5. Alternatively, an administrator can trigger a manual password reset link from the Admin Console under Users > Security.

## 2. Refund and Billing Policy
- Subscriptions can be canceled at any time from Settings > Billing.
- We offer a full refund within 14 days of purchase for annual plans.
- Monthly plans are non-refundable once the billing cycle begins, but users retain access until the end of the current paid billing period.
- For unauthorized charges, please attach the invoice ID and bank statement screenshot.

## 3. API Rate Limits & Error 429
- Free tier: 60 requests per minute.
- Pro tier: 600 requests per minute.
- Enterprise tier: Custom rate limits.
- When an application hits rate limits, HTTP status code 429 (Too Many Requests) is returned with a `Retry-After` header.
- Implement exponential backoff in client applications to avoid intermittent failures.

## 4. Integration & Webhooks
- Webhooks can be configured under Settings > Webhooks.
- Payloads are signed with an HMAC SHA-256 signature passed in the `X-SupportDesk-Signature` header.
- The webhook endpoint must return a `200 OK` within 5 seconds; otherwise, the request will be retried up to 3 times with exponential backoff.
