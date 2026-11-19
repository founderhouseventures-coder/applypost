# JobMail on Oracle Cloud Always Free

This is a **zero-monthly-infrastructure-cost, self-managed beta setup**, not an uptime guarantee or a substitute for paid production operations. Oracle Always Free capacity has no SLA, requires an account (usually card verification), may be unavailable in a home region, and can reclaim an underused VM. Keep the OCI account active and stay within the Console's **Always Free** quotas. Never upgrade or create a resource marked paid for this setup.

The stack runs Django, PostgreSQL, and Caddy on one Ubuntu Ampere A1 VM. Only Caddy publishes ports 80/443; PostgreSQL stays inside Docker's private bridge network. The app uses the founder Gmail SMTP account only for low-volume transactional mail. Razorpay remains test-only by default.

## Founder setup

1. Create or sign in to the one founder [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) account. Choose the home region carefully. Verify the new VM and boot volume are marked **Always Free** before creation; do not create trial-only paid resources. Oracle may request a payment card for identity verification; the free tier page says it is not charged unless the account is upgraded.
2. Create an Ubuntu 24.04 `VM.Standard.A1.Flex` VM within the current Always Free allowance (up to 2 OCPU and 12 GB total on A1). Attach an SSH public key. Paste `cloud-init.yaml` into the instance's cloud-init field. If A1 capacity is unavailable, wait or choose another available region before selecting any paid shape.
3. In the VCN security list/NSG, allow inbound TCP 80 and 443 from the internet. Allow TCP 22 only from the founder's current IP (`x.x.x.x/32`). Do not expose 5432. Wait for cloud-init to finish, then reconnect SSH so the `ubuntu` user gets the Docker group.
4. Register a hostname in [DuckDNS](https://www.duckdns.org/), point its A record to the VM's public IPv4, and wait for DNS to resolve. This shared free hostname is suitable for a beta URL, not branded email. Store the DuckDNS token outside the repo. Caddy obtains TLS automatically once DNS and ports 80/443 work.
5. Clone the public founder repo on the VM and prepare its private environment file:

   ```bash
   sudo mkdir -p /opt/jobmail
   sudo chown ubuntu:ubuntu /opt/jobmail
   git clone https://github.com/founderhouseventures-coder/applypost.git /opt/jobmail
   cd /opt/jobmail/saas
   chmod +x deploy/oci/*.sh
   ./deploy/oci/configure-env.sh
   ```

   The script generates independent random secrets and prompts for the hostname and Gmail App Password without printing them. Keep `.env` on the VM only; never commit it or paste it in chat.

6. Deploy and check the service:

   ```bash
   cd /opt/jobmail/saas
   ./deploy/oci/deploy.sh
   docker compose --project-directory /opt/jobmail/saas -f deploy/oci/compose.yaml logs --tail=100 web caddy
   curl --fail https://<your-hostname>/health/
   ```

   Expected health result: `{"status":"ok"}`. Then test signup and password reset mail, and test two synthetic accounts for data isolation. Do not use real customer data until those checks and the restore drill pass.

## Email and billing

- Gmail SMTP: set `EMAIL_HOST=smtp.gmail.com`, port `587`, TLS `true`, the founder sender address, and an App Password in `.env`. Use only for account activation/password-reset traffic; Google may throttle or restrict automated sending. Do not send marketing or bulk outreach from it.
- Razorpay remains `RAZORPAY_MODE=test` and `LIVE_BILLING_ENABLED=false`. Add test values only after merchant onboarding, test-plan creation, and test webhook setup. Test checkout, success, failure, cancellation, duplicate events, and account deletion. Live payments need Razorpay approval, valid business/legal/tax details, and a deliberate live-mode change by the founder.
- Do not use the free `isroot.in` hostname for monetized use; its terms say the free service is for personal, educational, and non-commercial use. DuckDNS terms permit lawful use but provide no uptime or domain ownership guarantee. A real custom domain and branded email may require spending money.

## Updates, backups, and recovery

Pull reviewed changes and rebuild:

```bash
cd /opt/jobmail
git pull --ff-only origin main
cd saas
./deploy/oci/deploy.sh
```

Schedule a daily local database dump with `crontab -e`:

```cron
0 2 * * * cd /opt/jobmail/saas && ./deploy/oci/backup.sh >> /var/log/jobmail-backup.log 2>&1
```

The script keeps 14 days of dumps on the same VM and sets private file permissions. **This is not an off-site backup.** Periodically copy an encrypted dump to a separate private device/account and run `restore.sh` against a disposable test database or maintenance window. Never keep customer dumps in GitHub or public object storage.

Rollback: identify the last known good commit with `git log --oneline -5`, check out that commit, rebuild with `./deploy/oci/deploy.sh`, then return to `main` after fixing the issue. Database schema downgrades are not automatic; restore a verified backup only after confirming the target database and downtime.

## Remaining limits

- One VM means one failure domain; no high availability, managed DB, SLA, or hands-off on-call.
- Oracle can reclaim idle Always Free compute; free capacity is not assured. Keep the account active and watch Oracle notices.
- The owner must operate patching, firewall, off-site backups, restore checks, domain renewal/availability, email secrets, and payment compliance.
- No live deployment is possible until the founder creates the OCI account/VM, configures DNS and Gmail App Password, and provides any merchant-owned Razorpay test values through the server environment.
