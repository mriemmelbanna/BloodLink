from django.contrib import admin
from .models import PatientProfile, PatientBloodRequest


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'full_name',
        'phone',
        'city',
        'created_at'
    )

    search_fields = (
        'full_name',
        'phone',
        'city'
    )

    list_filter = ('city',)


@admin.register(PatientBloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = (
        'patient_profile',
        'hospital',
        'blood_type',
        'units_needed',
        'urgency',
        'status',
        'created_at'
    )

    search_fields = (
        'patient_profile__full_name',
        'city',
        'blood_type'
    )

    list_filter = (
        'blood_type',
        'urgency',
        'status',
        'city'
    )