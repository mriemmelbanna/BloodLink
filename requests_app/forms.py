from django import forms
from .models import BloodRequest


class RequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = [
            "blood_type",
            "units_needed",
            "hospital",
            "urgency",
            "needed_by",
            "contact_phone",
            "notes",
        ]