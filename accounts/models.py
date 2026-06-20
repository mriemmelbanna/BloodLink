from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


BLOOD_TYPES = [
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
    ('O+', 'O+'), ('O-', 'O-'),
]

# =========================
# DONOR
# =========================
class Donor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="donor_profile")
    username =models.CharField(max_length=250)
    email = models.EmailField(max_length=250)

    phone = models.CharField(max_length=20)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    age = models.IntegerField()
    weight = models.IntegerField()
    address = models.TextField()
    city = models.CharField(max_length=50)
    latitude = models.DecimalField(
    max_digits=10,
    decimal_places=6,
    null=True,
    blank=True
    )
    longitude = models.DecimalField(
    max_digits=10,
    decimal_places=6,
    null=True,
    blank=True
    )
    has_no_restrictive_diseases = models.BooleanField(default=True)
    has_no_chronic_diseases = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        if self.age < 18 or self.age > 60:
           raise ValidationError("Age must be between 18 and 60.")

        if self.weight < 50:
           raise ValidationError("Weight must be at least 50 kg.")

        if not self.has_no_restrictive_diseases or not self.has_no_chronic_diseases:
           raise ValidationError("You are not eligible to donate blood.")
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
    def __str__(self):
        return self.user.username
# =========================
# PATIENT
# =========================
class Patient(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="patient_profile"
    )
    username =models.CharField(max_length=250)
    email = models.EmailField(max_length=250)

    phone = models.CharField(max_length=20)
    blood_type_needed = models.CharField(max_length=3, choices=BLOOD_TYPES)
    age = models.IntegerField()
    address = models.TextField()
    city = models.CharField(max_length=50)
    latitude = models.DecimalField(
    max_digits=10,
    decimal_places=6,
    null=True,
    blank=True
    )
    longitude = models.DecimalField(
    max_digits=10,
    decimal_places=6,
    null=True,
    blank=True
    )

    def __str__(self):
        return self.user.username


# =========================
# HOSPITAL
# =========================
class HospitalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="hospital_profile")
    hospital_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    address = models.TextField()
    license_file = models.FileField(
    upload_to="hospital_documents/licenses/",
    null=True,
    blank=True
      )

    official_docs = models.FileField(
    upload_to="hospital_documents/official_docs/",
    null=True,
    blank=True
     )
    latitude = models.DecimalField(
    max_digits=10,
    decimal_places=6,
    null=True,
    blank=True
    )
    longitude = models.DecimalField(
    max_digits=10,
    decimal_places=6,
    null=True,
    blank=True
    )
    def __str__(self):
        return self.hospital_name