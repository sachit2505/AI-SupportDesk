# Account Lockout Policy

## Lockout Triggers
To safeguard accounts against brute-force attacks and unauthorized access:
- An account is automatically locked after **5 consecutive failed login attempts**.
- A temporary security lock lasts for **30 minutes**.
- Users and administrators receive an automated security notification alert via email.

## How to Unlock Your Account
1. **Wait Out Duration**: The lock automatically releases after 30 minutes, allowing you to try again with valid credentials.
2. **Immediate Unlock via Password Reset**: Clicking "Forgot Password" on the login screen and completing email verification will instantly unlock the account and set a fresh password.
3. **Admin Assisted Unlock**: An organization administrator can unlock members manually from **Admin Console > Users > Select Member > Unlock Account**.

## Repeated Lockouts
If your account suffers persistent repeated lockouts without your involvement, your credentials may have been compromised elsewhere. We advise:
- Changing your password immediately.
- Enforcing Two-Factor Authentication (2FA).
- Revoking all active API tokens and browser sessions.
