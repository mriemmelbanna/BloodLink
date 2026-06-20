from django.db import models
from django.utils import timezone
import random
from accounts.models import HospitalProfile, Patient, BLOOD_TYPES


class BloodUnit(models.Model):

    class Status(models.TextChoices):
        COLLECTED = "COLLECTED", "Collected"
        TESTED = "TESTED", "Tested"
        AVAILABLE = "AVAILABLE", "Available"
        RESERVED = "RESERVED", "Reserved"
        EXPIRED = "EXPIRED", "Expired"
        DISCARDED = "DISCARDED", "Discarded"
        USED = "USED", "Used"

    class Source(models.TextChoices):
        COLLECTED = "Collected", "Collected"
        MANUAL = "Manual", "Manual"
        DONATION = "Donation", "Donation"

    hospital = models.ForeignKey(
        HospitalProfile,
        on_delete=models.CASCADE,
        related_name="blood_units"
    )

    unit_id = models.CharField(max_length=50, unique=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        default=Source.MANUAL
    )
    units = models.PositiveIntegerField(default=1)
    volume_ml = models.PositiveIntegerField(default=450)
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # توليد unit id تلقائي
        if not self.unit_id or self.unit_id.strip() == "":
            while True:
                new_id = str(
                    int(timezone.now().timestamp() * 1000)
                ) + str(random.randint(10, 99))

                if not BloodUnit.objects.filter(unit_id=new_id).exists():
                    self.unit_id = new_id
                    break

        # تغيير الحالة لو منتهي الصلاحية
        if self.expiry_date and self.expiry_date < timezone.localdate():
            self.status = self.Status.EXPIRED

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.unit_id} - {self.blood_type}"


class BloodRequest(models.Model):

    class RequestBy(models.TextChoices):
        HOSPITAL = "HOSPITAL", "Hospital"
        PATIENT = "PATIENT", "Patient"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        FULFILLED = "FULFILLED", "Fulfilled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Urgency(models.TextChoices):
        NORMAL = "NORMAL", "Normal"
        URGENT = "URGENT", "Urgent"
        CRITICAL = "CRITICAL", "Critical"

    requested_by = models.CharField(max_length=20, choices=RequestBy.choices)

    hospital = models.ForeignKey(
        HospitalProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="hospital_blood_requests"
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="blood_requests"
    )

    patient_name = models.CharField(max_length=150, blank=True, null=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    required_units = models.PositiveIntegerField(default=1)
    urgency = models.CharField(max_length=20, choices=Urgency.choices, default=Urgency.NORMAL)
    city = models.CharField(max_length=50)
    hospital_address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    target_donor = models.ForeignKey(
        "donors.DonorProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="targeted_requests"
    )
    scheduled_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.blood_type} - {self.requested_by}"


class Alert(models.Model):

    class AlertType(models.TextChoices):
        LOW_STOCK = "LOW_STOCK", "Low Stock"
        NEW_REQUEST = "NEW_REQUEST", "New Blood Request"
        CRITICAL_REQUEST = "CRITICAL_REQUEST", "Critical Request"
        DONOR_AVAILABLE = "DONOR_AVAILABLE", "Donor Available"

    hospital = models.ForeignKey(
        HospitalProfile,
        on_delete=models.CASCADE,
        related_name="alerts"
    )

    alert_type = models.CharField(max_length=50, choices=AlertType.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:50]


class HospitalAppointment(models.Model):
    hospital = models.ForeignKey(
        HospitalProfile,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    donor = models.ForeignKey(
        "donors.DonorProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    blood_request = models.ForeignKey(
        BloodRequest,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    appointment_time = models.DateTimeField()
    status = models.CharField(max_length=20, default="CONFIRMED")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hospital} - {self.appointment_time}"
