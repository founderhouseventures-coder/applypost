# JobMail SaaS: founder launch checklist

Code and deployment files are in the founder repo. The Django SaaS is not live yet. Use the free OCI path in [`deploy/oci/README.md`](deploy/oci/README.md); do not deploy the paid Render blueprint. Keep Razorpay in test mode until its complete lifecycle is verified.

## 1. Create the free OCI account and VM (about 20–40 minutes)

1. Sign in or create the one permitted [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) account under the founder identity. Oracle requires card verification; do not click **Upgrade** or create resources marked paid.
2. Pick the home region, choose an Always Free Ubuntu `VM.Standard.A1.Flex` instance, and stay within the displayed Always Free quotas. Capacity may be unavailable in the selected region.
3. Add an SSH public key. In the VCN security list, allow TCP `80` and `443`; restrict TCP `22` to your current public IP.
4. Register a [DuckDNS](https://www.duckdns.org/) hostname, point it to the VM public IP, and set it as `SITE_DOMAIN`. Keep the DuckDNS token private.
5. SSH to the VM and follow the repo's OCI guide. Run `deploy/oci/configure-env.sh` to privately enter the DuckDNS host and Gmail App Password and generate the app/database secrets; then deploy and verify `/health/`.

## 2. Configure transactional email (about 10 minutes)

1. In the founder Google account, create a dedicated Gmail App Password (requires 2-Step Verification).
2. Put it only in the VM's ignored `saas/.env` as `EMAIL_HOST_PASSWORD`. Use `smtp.gmail.com:587`, TLS on, and `founderhouse.ventures@gmail.com` as the sender.
3. Test signup activation and password reset emails. Gmail is for low-volume transactional mail only; respect its sending limit and stop if delivery is throttled.

## 3. Verify the product (about 15 minutes)

1. Create a synthetic account, verify activation, and test password reset.
2. Add, edit, export, and delete a synthetic application; check that a second account cannot see its data.
3. Confirm backup creation. Before real customers, copy an encrypted backup off the VM and complete a restore drill.

## 4. Enable payment tests (founder account details required)

1. Complete Razorpay merchant onboarding and legal/business checks.
2. In Test Mode, create the subscription plan and configure the test key ID, secret, plan ID, and webhook secret in `saas/.env`.
3. Test checkout, activation, failed payment, cancellation, duplicate webhooks, and account deletion. Keep `LIVE_BILLING_ENABLED=false`.
4. Interview five target users and validate the proposed ₹299/month price. It is a hypothesis, not proven pricing.

## 5. Before accepting real payments

- Provide accurate business identity, support contact, jurisdiction, refund/cancellation terms, and data-retention policy; have legal text reviewed.
- Complete the off-site backup and restore drill, review logs/security updates, and decide who will operate the VM.
- Finish Razorpay live-mode activation and tax review. Only then add live keys and explicitly enable live billing.
- Keep Gmail inbox sync disabled until Google's OAuth review requirements are satisfied. The SaaS only stores applications users enter themselves.

Never put passwords, API keys, webhook secrets, SSH private keys, OAuth files, or customer data in GitHub, chat, or this checklist.
