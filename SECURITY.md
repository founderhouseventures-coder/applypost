# Security policy

JobMail handles OAuth credentials and potentially sensitive email metadata locally. Do not include real message content, OAuth tokens, credential JSON, or spreadsheet exports in a public issue.

If GitHub's private vulnerability reporting is enabled for this repository, use the **Report a vulnerability** option in the Security tab. Otherwise, contact the repository owner through the public contact method on the GitHub profile. Include the affected version, impact, and a minimal reproduction with synthetic data.

The SaaS beta (`saas/`) does not collect Gmail tokens, email bodies, or payment card data. It stores user-entered job details, login records, a payment-provider subscription ID, and deduplicated webhook event IDs. Passwords are handled by Django's password hashers; application routes scope records to the authenticated owner. Razorpay webhooks are checked against raw request bytes before processing.

The project does not provide a security response-time guarantee. Revoke Google OAuth access and delete local token files if you suspect they were exposed. For the SaaS, reset account passwords and rotate affected application/payment credentials; do not send secrets or real user records in a public issue.
