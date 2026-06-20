from django.contrib import admin
from .models import DonorProfile, DonorActivity


class DonorActivityInline(admin.TabularInline):
    model = DonorActivity
    extra = 0


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'full_name',
        'blood_type',
        'city',
        'is_available',
        'weight_kg'
    )

    search_fields = (
        'user__username',
        'full_name',
        'phone',
        'city'
    )

    list_filter = (
        'blood_type',
        'city',
        'is_available'
    )

    readonly_fields = ('age',)

    inlines = [DonorActivityInline]


@admin.register(DonorActivity)
class DonorActivityAdmin(admin.ModelAdmin):
    list_display = (
        'donor',
        'title',
        'created_at'
    )

    search_fields = (
        'donor__full_name',
        'title'
    )