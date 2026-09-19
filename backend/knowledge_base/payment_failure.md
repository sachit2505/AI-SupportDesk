# Payment Failure Policy & Troubleshooting

## Common Causes of Failed Payments
- **Insufficient Funds**: The card balance is insufficient to process the subscription charge.
- **Card Expiration**: The expiration date on file has passed.
- **Fraud Detection or Bank Decline**: Many banking institutions require explicit authorization for recurring software charges.
- **Address Verification (AVS) Mismatch**: The billing zip/postal code entered does not match the cardholder address on file with the bank.

## Retry Schedule & Grace Period
- **4 Retry Attempts**: When a payment attempt fails, our billing processor automatically retries the charge after 2 days, 4 days, and 7 days.
- **10-Day Grace Period**: During the 10-day grace period, all account capabilities remain functional without disruption.
- **Suspension Notice**: If payment remains unresolved after 10 days, write access is temporarily suspended until an updated card is provided.

## How to Update Payment Details
1. Visit **Settings > Billing**.
2. Click **"Update Payment Method"**.
3. Input new credit card or payment credentials and click **"Retry Payment Now"**.
