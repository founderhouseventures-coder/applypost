from django.contrib import admin

from .models import (
    BillingEvent,
    BillingSubscription,
    JobApplication,
    MarketingPreference,
)

admin.site.register(JobApplication)
admin.site.register(BillingSubscription)
admin.site.register(BillingEvent)
admin.site.register(MarketingPreference)
