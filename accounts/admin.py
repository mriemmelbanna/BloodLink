from django.contrib import admin
from .models import Donor, Patient, HospitalProfile


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'blood_type',
        'age',
        'weight',
        'city',
        'is_available'
    )

    search_fields = (
        'user__username',
        'phone',
        'city',
        'blood_type'
    )

    list_filter = (
        'blood_type',
        'city',
        'has_no_restrictive_diseases',
        'has_no_chronic_diseases'
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'blood_type_needed',
        'age',
        'city'
    )

    search_fields = (
        'user__username',
        'phone',
        'city'
    )

    list_filter = (
        'blood_type_needed',
        'city'
    )


@admin.register(HospitalProfile)
class HospitalProfileAdmin(admin.ModelAdmin):
    list_display = (
        'hospital_name',
        'phone',
        'city'
    )

    search_fields = (
        'hospital_name',
        'phone',
        'city'
    )

    list_filter = ('city',)