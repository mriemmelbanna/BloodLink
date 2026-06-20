from django import forms

from hospitals.models import HospitalProfile
from .models import BloodUnit, BloodRequest


from django import forms
from accounts.models import HospitalProfile
from accounts.forms import EGYPT_CITIES


class HospitalProfileForm(forms.ModelForm):
    city = forms.ChoiceField(
        choices=EGYPT_CITIES,
        required=True
    )

    # 🔥 Checkbox لحذف الملفات
    remove_license = forms.BooleanField(required=False)
    remove_docs = forms.BooleanField(required=False)

    class Meta:
        model = HospitalProfile
        fields = [
           "hospital_name",
           "phone",
           "city",
           "address",
           "latitude",
           "longitude",
           "license_file",
           "official_docs",
        ]

class BloodUnitForm(forms.ModelForm):
    class Meta:
        model = BloodUnit
        fields = [ "blood_type", "volume_ml", "expiry_date", "status"]
        widgets = {
            "expiry_date": forms.DateInput(attrs={"type": "date"})
        }


class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = [
            "patient_name",
            "blood_type",
            "required_units",
            "urgency",
            "city",
            "hospital_address",
            "scheduled_time",
            "notes",
        ]

        widgets = {
            "scheduled_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-input"
                }
            )
        }


