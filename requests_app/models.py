from django.conf import settings
from django.db import models
from django.utils import timezone
from hospitals.models import HospitalProfile


# =========================
# PATIENT PROFILE
# =========================
class PatientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


# =========================
# BLOOD REQUEST
# =========================
class PatientBloodRequest(models.Model):

    class Urgency(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        URGENT = "URGENT", "Urgent"
        NORMAL = "NORMAL", "Normal"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        FULFILLED = "FULFILLED", "Fulfilled"
        CANCELLED = "CANCELLED", "Cancelled"

    patient_profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="blood_requests"
    )

    hospital = models.ForeignKey(
        HospitalProfile,
        on_delete=models.CASCADE,
        related_name="blood_requests"
    )

    BLOOD_TYPES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    blood_type = models.CharField(
        max_length=3,
        choices=BLOOD_TYPES
    )

    units_needed = models.PositiveIntegerField(default=1)

    city = models.CharField(max_length=100, blank=True)

    urgency = models.CharField(
        max_length=10,
        choices=Urgency.choices,
        default=Urgency.URGENT
    )

    needed_by = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN
    )

    contact_phone = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # =========================
    # Helpers
    # =========================
    @property
    def is_expired(self):
        return bool(self.needed_by and timezone.now() > self.needed_by)

    @property
    def hours_left(self):
        if not self.needed_by:
            return None
        delta = self.needed_by - timezone.now()
        return round(delta.total_seconds() / 3600, 1)

    def __str__(self):
        return f"{self.patient_profile} - {self.blood_type} ({self.urgency})"
class PatientAlert(models.Model):
    patient_profile = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="alerts"
    )

    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title