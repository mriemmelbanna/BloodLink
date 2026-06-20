from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Donor, Patient
from .models import HospitalProfile
from django.contrib.auth.forms import AuthenticationForm
from donors.models import DonorProfile

# ===== Class CSS موحد لكل الحقول =====
TAILWIND_INPUT_CLASS = "w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-red-600"


# ===== Login Form =====
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': TAILWIND_INPUT_CLASS,
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': TAILWIND_INPUT_CLASS,
            'placeholder': 'Password'
        })
    )

# ===== Donor Register Form =====



INPUT_CLASS = "form-input"


# 🇪🇬 Egypt Cities
EGYPT_CITIES = [
    ("Cairo", "Cairo"),
    ("Alexandria", "Alexandria"),
    ("Giza", "Giza"),
    ("Shubra El Kheima", "Shubra El Kheima"),
    ("Port Said", "Port Said"),
    ("Suez", "Suez"),
    ("Luxor", "Luxor"),
    ("Aswan", "Aswan"),
    ("Asyut", "Asyut"),
    ("Mansoura", "Mansoura"),
    ("Tanta", "Tanta"),
    ("Zagazig", "Zagazig"),
    ("Ismailia", "Ismailia"),
    ("Faiyum", "Faiyum"),
    ("Damietta", "Damietta"),
    ("Minya", "Minya"),
    ("Beni Suef", "Beni Suef"),
    ("Qena", "Qena"),
    ("Sohag", "Sohag"),
    ("Hurghada", "Hurghada"),
    ("Sharm El Sheikh", "Sharm El Sheikh"),
]


class DonorRegisterForm(UserCreationForm):

    # ======================
    # USER INFO
    # ======================
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True)

    blood_type = forms.ChoiceField(
        choices=Donor._meta.get_field('blood_type').choices
    )

    age = forms.IntegerField(required=True)
    weight = forms.IntegerField(required=True)

    address = forms.CharField(widget=forms.Textarea)

    city = forms.ChoiceField(
        choices=EGYPT_CITIES,
        required=True
    )
    latitude = forms.DecimalField(
        required=False,
        max_digits=18,
        decimal_places=6,
        widget=forms.HiddenInput()
   )

    longitude = forms.DecimalField(
        required=False,
        max_digits=18,
        decimal_places=6,
        widget=forms.HiddenInput()
    )

    # ======================
    # MEDICAL CHECKS
    # ======================
    no_restrictive_diseases = forms.BooleanField(required=False)
    no_chronic_diseases = forms.BooleanField(required=False)

    # ======================
    # META
    # ======================
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    # ======================
    # STYLING
    # ======================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': INPUT_CLASS,
            'placeholder': 'Enter username'
        })

        self.fields['email'].widget.attrs.update({
            'class': INPUT_CLASS,
            'placeholder': 'Enter email'
        })

        self.fields['password1'].widget.attrs.update({
            'class': INPUT_CLASS,
            'placeholder': 'Password'
        })

        self.fields['password2'].widget.attrs.update({
            'class': INPUT_CLASS,
            'placeholder': 'Confirm Password'
        })

        self.fields['phone'].widget.attrs.update({
            'class': INPUT_CLASS,
            'placeholder': 'Enter phone number'
        })

        self.fields['age'].widget.attrs.update({
            'class': INPUT_CLASS,
            'placeholder': 'Enter age'
        })

        self.fields['weight'].widget.attrs.update({
            'class': INPUT_CLASS,
            'placeholder': 'Enter weight'
        })

        self.fields['address'].widget.attrs.update({
            'class': INPUT_CLASS,
            'placeholder': 'Enter address'
        })

        self.fields['city'].widget.attrs.update({
            'class': INPUT_CLASS
        })

    # ======================
    # VALIDATION
    # ======================

    def clean_age(self):

        age = self.cleaned_data.get('age')

        if age is None:
            return age

        if age < 18:

            raise forms.ValidationError(
                "Not eligible: donor age must be 18 years or older."
            )

        if age > 60:

            raise forms.ValidationError(
                "Not eligible: donor age must be below 60 years."
            )

        return age

    def clean_weight(self):

        weight = self.cleaned_data.get('weight')

        if weight is None:
            return weight

        if weight < 50:

            raise forms.ValidationError(
                "Not eligible: donor weight must be at least 50 kg."
            )

        return weight
    def clean_password1(self):
        password = self.cleaned_data.get("password1")

        if password and len(password) < 8:
            raise forms.ValidationError(
                "Password must contain at least 8 characters."
           )
        return password

    def clean(self):

        cleaned_data = super().clean()

        restrictive = cleaned_data.get('no_restrictive_diseases')
        chronic = cleaned_data.get('no_chronic_diseases')

        # ======================
        # RESTRICTIVE DISEASES
        # ======================
        if restrictive is False:

            self.add_error(
                'no_restrictive_diseases',

                "Not eligible: donor has restrictive diseases that prevent blood donation."
            )

        # ======================
        # CHRONIC DISEASES
        # ======================
        if chronic is False:

            self.add_error(
                'no_chronic_diseases',

                "Not eligible: donor has chronic diseases."
            )

        return cleaned_data

    # ======================
    # SAVE LOGIC
    # ======================
    def save(self, commit=True):

        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:

            user.save()

            Donor.objects.update_or_create(
                user=user,
                defaults={
                    "username":user.username,
                    "email":user.email,
                    "phone": self.cleaned_data['phone'],
                    "blood_type": self.cleaned_data['blood_type'],
                    "age": self.cleaned_data['age'],
                    "weight": self.cleaned_data['weight'],
                    "address": self.cleaned_data['address'],
                    "city": self.cleaned_data['city'],
                    
                    "has_no_restrictive_diseases": self.cleaned_data['no_restrictive_diseases'],
                    "has_no_chronic_diseases": self.cleaned_data['no_chronic_diseases'],
                    "latitude": self.cleaned_data.get("latitude"),
                    "longitude": self.cleaned_data.get("longitude"),
                }
            )

            DonorProfile.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": user.username,
                    "phone": self.cleaned_data['phone'],
                    "blood_type": self.cleaned_data['blood_type'],
                    "weight_kg": self.cleaned_data['weight'],
                    "address": self.cleaned_data['address'],
                    "city": self.cleaned_data['city'],
                    "latitude": self.cleaned_data.get("latitude"),
                    "longitude": self.cleaned_data.get("longitude"),
                    "is_available": True,
                }
            )

        return user
# ===== Patient Register Form =====
class PatientRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': TAILWIND_INPUT_CLASS, 'placeholder': 'Enter your email'})
    )
    phone = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS, 'placeholder': 'Enter your phone'})
    )
    blood_type_needed = forms.ChoiceField(
        choices=Patient._meta.get_field('blood_type_needed').choices,
        widget=forms.Select(attrs={'class': TAILWIND_INPUT_CLASS})
    )
    age = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class': TAILWIND_INPUT_CLASS, 'placeholder': 'Enter your age'})
    )
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': TAILWIND_INPUT_CLASS, 'placeholder': 'Enter your address', 'rows': 3})
    )
    city = forms.ChoiceField(
      choices=EGYPT_CITIES,
      required=True,
      widget=forms.Select(attrs={'class': TAILWIND_INPUT_CLASS})
      ) 
    latitude = forms.DecimalField(required=False, widget=forms.HiddenInput())
    longitude = forms.DecimalField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': TAILWIND_INPUT_CLASS, 'placeholder': 'Enter username'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 🔥 ده المهم
        self.fields['password1'].widget.attrs.update({
            'class': TAILWIND_INPUT_CLASS,
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': TAILWIND_INPUT_CLASS,
            'placeholder': 'Confirm Password'
        })

# ===== Hospital Register Form =====
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
INPUT_CLASS = "form-input"


User = get_user_model()


class HospitalRegisterForm(UserCreationForm):
    hospital_name = forms.CharField(required=True)
    phone = forms.CharField(required=True)

    city = forms.ChoiceField(
        choices=EGYPT_CITIES,
        required=True
    )
    latitude = forms.DecimalField(required=False, widget=forms.HiddenInput())
    longitude = forms.DecimalField(required=False, widget=forms.HiddenInput())

    address = forms.CharField(required=True, widget=forms.Textarea)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2",
            "hospital_name",
            "phone",
            "city",
            "address",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in [
            "username",
            "email",
            "password1",
            "password2",
            "hospital_name",
            "phone",
            "city",
            "address",
        ]:
            self.fields[field_name].widget.attrs.update({
                "class": INPUT_CLASS
            })

        self.fields["username"].widget.attrs.update({
            "placeholder": "Enter username"
        })

        self.fields["email"].widget.attrs.update({
            "placeholder": "Enter email"
        })

        self.fields["password1"].widget.attrs.update({
            "placeholder": "Password"
        })

        self.fields["password2"].widget.attrs.update({
            "placeholder": "Confirm Password"
        })

        self.fields["hospital_name"].widget.attrs.update({
            "placeholder": "Enter hospital name"
        })

        self.fields["phone"].widget.attrs.update({
            "placeholder": "Enter phone"
        })

        self.fields["address"].widget.attrs.update({
            "placeholder": "Enter address",
            "rows": 3
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        

        if commit:
            user.save()

            HospitalProfile.objects.create(
                user=user,
                hospital_name=self.cleaned_data["hospital_name"],
                phone=self.cleaned_data["phone"],
                city=self.cleaned_data["city"],
                address=self.cleaned_data["address"],
                latitude = self.cleaned_data.get("latitude"),
                longitude = self.cleaned_data.get("longitude"),
                
            )

        return user