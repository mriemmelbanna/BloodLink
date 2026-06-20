from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class DonorProfile(models.Model):
    BLOOD_TYPES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
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

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Personal
    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(
    max_length=100,
    choices=EGYPT_CITIES,
    blank=True,
    null=True
   )
     
    # Medical
    blood_type = models.CharField(max_length=5, choices=BLOOD_TYPES, blank=True, null=True)
    weight_kg = models.PositiveIntegerField(null=True, blank=True)
    last_donation_date = models.DateField(null=True, blank=True)
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)

    # Availability Settings
    is_available = models.BooleanField(default=True)
    max_distance_km = models.PositiveIntegerField(default=15)
    #location
    latitude = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"DonorProfile({self.user.username})"

    # ✅ حساب العمر
    @property
    def age(self):
        if not self.date_of_birth:
            return None
        return (timezone.now().date() - self.date_of_birth).days // 365

    # ✅ Validation
    def clean(self):
        # السن
        if self.date_of_birth:
            age = self.age
            if age < 18 or age > 60:
                raise ValidationError("العمر لازم يكون بين 18 و 60 سنة.")

        # الوزن
        if self.weight_kg is not None and self.weight_kg < 50:
            raise ValidationError("الوزن لازم يكون على الأقل 50 كجم.")

    # ✅ مهم جدًا عشان validation تشتغل مع save
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
class DonorActivity(models.Model):
    donor = models.ForeignKey(
        DonorProfile,
        on_delete=models.CASCADE,
        related_name="activities"
    )
    title = models.CharField(max_length=150)
    details = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title