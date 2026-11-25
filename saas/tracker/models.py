from datetime import timedelta
from uuid import uuid4

from django.conf import settings
from django.db import models


class JobApplication(models.Model):
    class Status(models.TextChoices):
        SAVED = "saved", "Saved"
        APPLIED = "applied", "Applied"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    company = models.CharField(max_length=120)
    role = models.CharField(max_length=160)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.SAVED
    )
    source = models.CharField(max_length=120, blank=True)
    job_url = models.URLField(max_length=500, blank=True)
    applied_on = models.DateField(null=True, blank=True)
    follow_up_on = models.DateField(null=True, blank=True)
    resume_version = models.CharField(max_length=80, blank=True)
    notes = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "company"]
        indexes = [models.Index(fields=["user", "status", "-updated_at"])]

    def __str__(self):
        return f"{self.role} at {self.company}"


class BillingSubscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="billing_subscription",
    )
    provider_id = models.CharField(max_length=80, unique=True)
    status = models.CharField(max_length=24, default="created")
    provider_mode = models.CharField(max_length=8, default="test")
    plan_id = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class BillingEvent(models.Model):
    event_id = models.CharField(max_length=120, unique=True)
    event_type = models.CharField(max_length=100)
    received_at = models.DateTimeField(auto_now_add=True)


class MarketingPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marketing_preference",
    )
    opted_in = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


class PilotTrial(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pilot_trial"
    )
    started_at = models.DateTimeField(auto_now_add=True)
    receipt = models.UUIDField(default=uuid4, editable=False, unique=True)
    order_id = models.CharField(max_length=80, blank=True)

    @property
    def ends_at(self):
        return self.started_at + timedelta(days=14)
