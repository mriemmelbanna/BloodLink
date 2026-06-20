from django.contrib import admin
from .models import BloodUnit, BloodRequest


@admin.register(BloodUnit)
class BloodUnitAdmin(admin.ModelAdmin):
    list_display = (
        'unit_id',
        'hospital',
        'blood_type',
        'volume_ml',
        'status',
        'expiry_date'
    )

    search_fields = (
        'unit_id',
        'hospital__hospital_name'
    )

    list_filter = (
        'blood_type',
        'status',
        'expiry_date'
    )


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        'blood_type',
        'requested_by',
        'urgency',
        'city',
        'status',
        'created_at'
    )

    search_fields = (
        'patient_name',
        'city'
    )

    list_filter = (
        'blood_type',
        'urgency',
        'status',
        'requested_by'
    )


