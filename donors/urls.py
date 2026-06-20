from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.donor_dashboard, name="donor_dashboard"),
    path("profile/", views.donor_profile, name="donor_profile"),
    path("profile/edit/", views.donor_profile_edit, name="donor_profile_edit"),
    path("alerts/", views.donor_alerts, name="donor_alerts"),
    path("settings/availability/", views.donor_availability_settings, name="donor_settings"),
    path("alerts/<int:request_id>/respond/", views.respond_to_request, name="respond_to_request"),
    path("list/", views.donor_list, name="donor_list"),  # ✅ الجديد
    path("request/<int:donor_id>/", views.request_donor, name="request_donor"),
    path(
    "request-hospital/<int:hospital_id>/",
    views.request_hospital,
    name="request_hospital"
),
    path("nearby-requests/", views.donor_nearby_requests, name="donor_nearby_requests"),
    path(
    "request/<int:request_id>/done/",
    views.complete_donation,
    name="complete_donation"
),
]