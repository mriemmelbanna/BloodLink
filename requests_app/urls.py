from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.patient_dashboard, name="patient_dashboard"),
    path("profile/", views.patient_profile, name="patient_profile"),
    path("profile/edit/", views.patient_edit, name="patient_edit"),

    path("new/", views.create_request, name="create_request"),
    path("my/", views.patient_requests, name="patient-requests"),
    path("<int:pk>/", views.request_details, name="request_details"),
    path("<int:pk>/cancel/", views.cancel_request, name="cancel_request"),
    path(
    "donor/<int:donor_id>/",
    views.donor_details_patient,
    name="donor_details_patient"
),
]