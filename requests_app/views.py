from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from accounts.forms import EGYPT_CITIES
from hospitals.models import HospitalProfile

from .models import PatientProfile
from hospitals.models import BloodRequest, Alert
from accounts.models import Patient
from .models import PatientBloodRequest, PatientProfile
from hospitals.models import BloodRequest , Alert
from accounts.models import Patient
from .models import PatientAlert
from donors.models import DonorProfile
# =========================
# HELPER: GET PATIENT PROFILE
# =========================
def _get_patient_profile(user):
    profile, _ = PatientProfile.objects.get_or_create(user=user)
    return profile


# =========================
# PATIENT DASHBOARD
# =========================
@login_required
def patient_dashboard(request):

    pprofile = _get_patient_profile(request.user)

    from accounts.models import Patient
    from hospitals.models import BloodRequest

    patient_obj = Patient.objects.filter(
        user=request.user
    ).first()

    # =========================
    # OLD PATIENT REQUESTS
    # =========================
    old_requests = PatientBloodRequest.objects.filter(
        patient_profile=pprofile
    )

    # =========================
    # FIND BLOOD REQUESTS
    # =========================
    blood_requests = BloodRequest.objects.filter(
        patient=patient_obj
    )

    # =========================
    # OPEN REQUESTS COUNT
    # =========================
    old_open = old_requests.filter(
        status=PatientBloodRequest.Status.OPEN
    ).count()

    blood_open = blood_requests.filter(
        status__in=[
            BloodRequest.Status.PENDING,
            BloodRequest.Status.ACCEPTED,
        ]
    ).count()

    open_count = old_open + blood_open

    # =========================
    # TOTAL REQUESTS
    # =========================
    total_count = old_requests.count() + blood_requests.count()

    # =========================
    # RECENT REQUEST
    # =========================
    all_requests = list(old_requests) + list(blood_requests)

    all_requests = sorted(
        all_requests,
        key=lambda x: x.created_at,
        reverse=True
    )

    last_request = all_requests[0] if all_requests else None

    # =========================
    # ALERTS
    # =========================
    alerts = PatientAlert.objects.filter(
        patient_profile=pprofile
    ).order_by("-created_at")[:5]

    # Mark all unread alerts as read when patient visits dashboard
    PatientAlert.objects.filter(patient_profile=pprofile, is_read=False).update(is_read=True)

    return render(request, "requests_app/patient_dashboard.html", {
        "pprofile": pprofile,
        "open_count": open_count,
        "total_count": total_count,
        "last_request": last_request,
        "alerts": alerts,
        "active_tab": "patient_dashboard"
    })

# =========================
# PATIENT PROFILE
# =========================
@login_required
def patient_profile(request):
    pprofile = _get_patient_profile(request.user)

    return render(request, "requests_app/patient_profile.html", {
        "pprofile": pprofile,
        "active_tab": "patient_profile"
    })


# =========================
# PATIENT EDIT PROFILE
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def patient_edit(request):
    pprofile = _get_patient_profile(request.user)

    if request.method == "POST":
        pprofile.full_name = request.POST.get("full_name", "").strip()
        pprofile.phone = request.POST.get("phone", "").strip()
        pprofile.address = request.POST.get("address", "").strip()
        pprofile.city = request.POST.get("city", "").strip()

        lat = request.POST.get("latitude", "").strip()
        lng = request.POST.get("longitude", "").strip()

        pprofile.latitude = request.POST.get("latitude") or None
        pprofile.longitude = request.POST.get("longitude") or None

        pprofile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("patient_profile")

    return render(request, "requests_app/patient_edit.html", {
        "pprofile": pprofile,
        "egypt_cities": EGYPT_CITIES,
        "active_tab": "patient_profile"
    })


# =========================
# CREATE BLOOD REQUEST
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def create_request(request):
    pprofile = _get_patient_profile(request.user)
    hospitals = HospitalProfile.objects.all()

    if request.method == "POST":
        blood_type = request.POST.get("blood_type", "").strip()
        units_needed = request.POST.get("units_needed", "1")
        hospital_id = request.POST.get("hospital")
        city = request.POST.get("city", "").strip()
        urgency = request.POST.get("urgency", PatientBloodRequest.Urgency.URGENT).strip()
        notes = request.POST.get("notes", "").strip()
        contact_phone = request.POST.get("contact_phone", "").strip()
        scheduled_time = request.POST.get("scheduled_time") or None

        if not blood_type:
            messages.error(request, "Blood type is required.")
            return redirect("create_request")

        if not hospital_id:
            messages.error(request, "Hospital is required.")
            return redirect("create_request")

        try:
            units_needed_int = int(units_needed)
        except ValueError:
            units_needed_int = 1

        hospital = get_object_or_404(HospitalProfile, id=hospital_id)
        patient_obj = Patient.objects.filter(user=request.user).first()

        hospital_request = BloodRequest.objects.create(
            requested_by=BloodRequest.RequestBy.PATIENT,
            hospital=hospital,
            patient=patient_obj,
            patient_name=pprofile.full_name or request.user.username,
            blood_type=blood_type,
            required_units=units_needed_int,
            urgency=urgency,
            city=city or pprofile.city or hospital.city,
            hospital_address=hospital.address,
            notes=notes,
            status=BloodRequest.Status.PENDING,
            scheduled_time=scheduled_time,
        )

        Alert.objects.create(
            hospital=hospital,
            alert_type=Alert.AlertType.NEW_REQUEST,
            message=f"New patient request: {hospital_request.patient_name} needs {hospital_request.required_units} unit(s) of {hospital_request.blood_type}."
        )

        messages.success(request, "Blood request submitted successfully.")
        return redirect("patient-requests")

    return render(request, "requests_app/form.html", {
        "pprofile": pprofile,
        "hospitals": hospitals,
        "urgency_choices": PatientBloodRequest.Urgency.choices,
        "defaults": {
            "city": pprofile.city,
            "contact_phone": pprofile.phone,
            "urgency": PatientBloodRequest.Urgency.URGENT,
            "units_needed": 1,
        },
        "active_tab": "create_request"
    })

# =========================
# PATIENT REQUESTS LIST
# =========================
@login_required
def patient_requests(request):

    pprofile = _get_patient_profile(request.user)

    patient_obj = Patient.objects.filter(
        user=request.user
    ).first()

    # =========================
    # AUTO-CANCEL EXPIRED REQUESTS
    # =========================
    now = timezone.now()

    # Cancel expired BloodRequests (have scheduled_time in the past)
    expired_blood = BloodRequest.objects.filter(
        patient=patient_obj,
        status__in=[BloodRequest.Status.PENDING, BloodRequest.Status.ACCEPTED],
        scheduled_time__lt=now,
        scheduled_time__isnull=False,
    )
    for r in expired_blood:
        r.status = BloodRequest.Status.CANCELLED
        r.save(update_fields=["status"])
        PatientAlert.objects.create(
            patient_profile=pprofile,
            title="Request Auto-Cancelled",
            message=f"Your {r.blood_type} request was automatically cancelled because the scheduled time has passed."
        )

    # Cancel expired PatientBloodRequests (have needed_by in the past)
    expired_patient = PatientBloodRequest.objects.filter(
        patient_profile=pprofile,
        status=PatientBloodRequest.Status.OPEN,
        needed_by__lt=now,
        needed_by__isnull=False,
    )
    for r in expired_patient:
        r.status = PatientBloodRequest.Status.CANCELLED
        r.save(update_fields=["status"])
        PatientAlert.objects.create(
            patient_profile=pprofile,
            title="Request Auto-Cancelled",
            message=f"Your {r.blood_type} request was automatically cancelled because the scheduled time has passed."
        )

    # =========================
    # OLD REQUESTS
    # =========================
    old_requests = list(
        PatientBloodRequest.objects
        .select_related("hospital", "patient_profile")
        .filter(patient_profile=pprofile)
    )

    # =========================
    # FIND BLOOD REQUESTS
    # =========================
    blood_requests = list(
        BloodRequest.objects
        .select_related("hospital", "patient")
        .filter(patient=patient_obj)
    )

    # =========================
    # NORMALIZE + MERGE + SORT
    # =========================
    # Add missing attrs to PatientBloodRequest so template handles both types uniformly
    for r in old_requests:
        r.required_units = r.units_needed
        r.scheduled_time = getattr(r, 'needed_by', None)
        if not hasattr(r, 'target_donor'):
            r.target_donor = None

    all_requests = old_requests + blood_requests

    all_requests = sorted(
        all_requests,
        key=lambda x: x.created_at,
        reverse=True
    )

    return render(request, "requests_app/patient_requests.html", {
        "requests": all_requests,
        "active_tab": "patient_requests"
    })


# =========================
# REQUEST DETAILS
# =========================
@login_required
def request_details(request, pk):
    pprofile = _get_patient_profile(request.user)

    br = get_object_or_404(
        PatientBloodRequest,
        pk=pk,
        patient_profile=pprofile
    )

    return render(request, "requests_app/request_details.html", {
        "req": br,
        "active_tab": "patient_requests"
    })


# =========================
# CANCEL REQUEST
# =========================
@login_required
@require_http_methods(["POST"])
def cancel_request(request, pk):
    pprofile = _get_patient_profile(request.user)
    patient_obj = Patient.objects.filter(user=request.user).first()

    # Try PatientBloodRequest first (old requests)
    br = PatientBloodRequest.objects.filter(pk=pk, patient_profile=pprofile).first()
    if br:
        if br.status != PatientBloodRequest.Status.OPEN:
            messages.info(request, "Only OPEN requests can be cancelled.")
            return redirect("patient-requests")
        br.status = PatientBloodRequest.Status.CANCELLED
        br.save(update_fields=["status"])
        messages.success(request, "Request cancelled.")
        return redirect("patient-requests")

    # Try BloodRequest (new requests)
    br = BloodRequest.objects.filter(pk=pk, patient=patient_obj).first()
    if br:
        if br.status not in [BloodRequest.Status.PENDING, BloodRequest.Status.ACCEPTED]:
            messages.info(request, "This request cannot be cancelled.")
            return redirect("patient-requests")
        br.status = BloodRequest.Status.CANCELLED
        br.save(update_fields=["status"])
        messages.success(request, "Request cancelled.")
        return redirect("patient-requests")

    messages.error(request, "Request not found.")
    return redirect("patient-requests")
@login_required
def donor_details_patient(request, donor_id):

    donor = get_object_or_404(
        DonorProfile,
        id=donor_id
    )

    return render(request, "requests_app/donor_details_patient.html", {
        "donor": donor,
        "active_tab": "patient_requests"
    })