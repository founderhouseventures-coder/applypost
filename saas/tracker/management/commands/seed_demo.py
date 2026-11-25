from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from tracker.models import JobApplication

ROWS = [
    ("Northstar Labs", "Product Designer", "interview", "LinkedIn", "Design v3"),
    ("Fieldnote", "Frontend Engineer", "applied", "Referral", "Frontend v2"),
    ("Monograph", "UX Engineer", "saved", "Company site", ""),
    ("Brightpath", "Data Analyst", "applied", "Naukri", "Data v1"),
    ("Quillwork", "Backend Engineer", "rejected", "Wellfound", "Backend v2"),
    ("Harbor Health", "Product Manager", "offer", "Referral", "PM v1"),
    ("Tinyloop", "Full Stack Developer", "applied", "LinkedIn", "Frontend v2"),
    ("Orbit Retail", "QA Engineer", "withdrawn", "Indeed", "QA v1"),
    ("Lumen Finance", "Data Scientist", "interview", "Company site", "Data v1"),
    ("Cobalt Studio", "UI Designer", "applied", "Dribbble", "Design v3"),
    ("Pinecrest", "Support Engineer", "saved", "LinkedIn", ""),
    ("Kestrel AI", "ML Engineer", "applied", "Referral", "Data v1"),
    ("Saffron Foods", "Growth Analyst", "rejected", "Naukri", "Data v1"),
    ("Vantage Cloud", "DevOps Engineer", "interview", "Wellfound", "Backend v2"),
    ("Meridian Ed", "Content Designer", "applied", "LinkedIn", "Design v3"),
    ("Arcadia Labs", "Platform Engineer", "applied", "Company site", "Backend v2"),
    ("Juniper Pay", "Android Developer", "saved", "Indeed", ""),
    ("Nimbus HR", "Product Analyst", "applied", "Referral", "PM v1"),
    ("Redwood Mobility", "iOS Developer", "interview", "LinkedIn", "Frontend v2"),
    ("Sable Security", "Security Analyst", "applied", "Company site", "Backend v2"),
    ("Willow Media", "Video Editor", "rejected", "Indeed", "Design v3"),
    ("Echo Logistics", "Operations Analyst", "applied", "Naukri", "Data v1"),
    ("Granite Bank", "Business Analyst", "saved", "LinkedIn", ""),
    ("Helix Bio", "Research Engineer", "applied", "Referral", "Data v1"),
]


class Command(BaseCommand):
    help = "Create the synthetic demo user and applications (safe to rerun)."

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(
            username="demo", defaults={"email": "demo@example.com"}
        )
        user.set_unusable_password()
        user.save()
        today = timezone.localdate()
        user.applications.all().delete()
        JobApplication.objects.bulk_create(
            JobApplication(
                user=user,
                company=company,
                role=role,
                status=status,
                source=source,
                resume_version=resume,
                applied_on=None
                if status == "saved"
                else today - timedelta(days=3 * i + 1),
                follow_up_on=today + timedelta(days=i % 7 - 2)
                if status in {"applied", "interview"}
                else None,
                notes="Synthetic demo row",
            )
            for i, (company, role, status, source, resume) in enumerate(ROWS)
        )
        self.stdout.write(f"Seeded demo user with {len(ROWS)} applications")
