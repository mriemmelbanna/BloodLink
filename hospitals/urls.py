from django.urls import path
from . import views

urlpatterns = [
    path("logout/", views.hospital_logout, name="hospital_logout"),

    path("dashboard/", views.hospital_dashboard, name="hospital_dashboard"),

    path("profile/", views.hospital_profile, name="hospital_profile"),
    path("profile/edit/", views.hospital_edit_profile, name="hospital_edit_profile"),

    path("inventory/", views.inventory_list, name="hospital_inventory"),
    path("inventory/add/", views.inventory_add, name="hospital_inventory_add"),
    path("inventory/<int:pk>/status/", views.inventory_update_status, name="hospital_inventory_status"),
    path("inventory/<int:pk>/discard/", views.inventory_discard, name="hospital_inventory_discard"),

    path("donors/", views.available_donors, name="hospital_available_donors"),

    path("requests/", views.blood_request_list, name="hospital_requests"),
    path("requests/create/", views.blood_request_create, name="hospital_request_create"),

   

    path("alerts/", views.hospital_alerts, name="hospital_alerts"),
    path("settings/", views.hospital_settings, name="hospital_settings"),
    path("profile/remove-license/", views.remove_license, name="remove_license"),
    path("profile/remove-docs/", views.remove_docs, name="remove_docs"),
    path("donors/<int:donor_id>/", views.donor_detail, name="donor_detail"),
    path('inventory-reports/', views.inventory_reports, name='inventory_reports'),
    path("requests/<int:pk>/cancel/", views.blood_request_cancel, name="hospital_request_cancel"),
    path("patient-request/<int:request_id>/accept/", views.accept_patient_request, name="accept_patient_request"),
    path("patient-request/<int:request_id>/reject/", views.reject_patient_request, name="reject_patient_request"),
    path("patient-request/<int:request_id>/done/", views.done_patient_request, name="done_patient_request"), 
    path(
    "appointments/<int:appointment_id>/collected/",
    views.mark_appointment_collected,
    name="mark_appointment_collected"
),
]