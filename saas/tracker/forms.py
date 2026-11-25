from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import JobApplication


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254)
    product_updates = forms.BooleanField(required=False)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = (
            "company",
            "role",
            "status",
            "source",
            "job_url",
            "applied_on",
            "follow_up_on",
            "resume_version",
            "notes",
        )
        widgets = {
            "applied_on": forms.DateInput(attrs={"type": "date"}),
            "follow_up_on": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
