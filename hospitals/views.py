from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from accounts.models import HospitalProfile, Donor, BLOOD_TYPES
from .forms import BloodUnitForm, HospitalProfileForm, BloodRequestForm
from .models import BloodUnit, BloodRequest, Alert
from math import radians, sin, cos, sqrt, atan2
from donors.models import DonorProfile
from accounts.models import BLOOD_TYPES
from .models import HospitalAppointment
from .models import HospitalAppointment
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import BloodRequest, BloodUnit, Alert
from datetime import date ,timedelta
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import uuid
from .models import HospitalAppointment, BloodUnit, Alert
from requests_app.models import PatientProfile, PatientAlert


def calculate_distance_km(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2:
        return None

    r = 6371

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(r * c, 2)

# =========================
# GET HOSPITAL PROFILE
# =========================
def _get_hospital_profile(user):
    try:
        return user.hospital_profile
    except HospitalProfile.DoesNotExist:
        return None


# =========================
# LOGOUT
# =========================
@login_required
def hospital_logout(request):
    logout(request)
    return redirect("login")


# =========================
# DASHBOARD
# =========================
@login_required
def hospital_dashboard(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    # =========================
    # AUTO-CANCEL EXPIRED APPOINTMENTS (donor didn't show up)
    # =========================
    now = timezone.now()
    expired_appointments = HospitalAppointment.objects.filter(
        hospital=hp,
        status="CONFIRMED",
        appointment_time__lt=now,
    )
    for appt in expired_appointments:
        appt.status = "CANCELLED"
        appt.save(update_fields=["status"])
        # Notify hospital
        Alert.objects.create(
            hospital=hp,
            alert_type=Alert.AlertType.NEW_REQUEST,
            message=f"Appointment with donor {appt.donor.user.username if appt.donor else 'Unknown'} was automatically cancelled — donor did not show up."
        )
        # Mark blood request back to PENDING so hospital can reassign
        if appt.blood_request and appt.blood_request.status == BloodRequest.Status.ACCEPTED:
            appt.blood_request.status = BloodRequest.Status.PENDING
            appt.blood_request.save(update_fields=["status"])

    units = BloodUnit.objects.filter(hospital=hp).order_by("-created_at")[:10]
    requests = BloodRequest.objects.filter(hospital=hp).order_by("-created_at")[:5]
   
    alerts = Alert.objects.filter(hospital=hp, is_read=False).order_by("-created_at")[:5]

    stats = {
        "total": BloodUnit.objects.filter(hospital=hp).count(),
        "available": BloodUnit.objects.filter(
            hospital=hp,
            status=BloodUnit.Status.AVAILABLE
        ).count(),
        "expired": BloodUnit.objects.filter(
            hospital=hp,
            status=BloodUnit.Status.EXPIRED
        ).count(),
        "discarded": BloodUnit.objects.filter(
            hospital=hp,
            status=BloodUnit.Status.DISCARDED
        ).count(),
        "requests": BloodRequest.objects.filter(hospital=hp).count(),
        
        "alerts": Alert.objects.filter(hospital=hp, is_read=False).count(),
    }

    inventory_summary = []

    for value, label in BLOOD_TYPES:
        count = BloodUnit.objects.filter(
            hospital=hp,
            blood_type=value,
            status=BloodUnit.Status.AVAILABLE
        ).count()

        if count > 10:
            level = "Good"
            message = "Stock is sufficient."
            css_class = "good"

        elif count < 5:
            level = "Low"
            message = "You need to create a blood request."
            css_class = "low"

            Alert.objects.get_or_create(
                hospital=hp,
                alert_type=Alert.AlertType.LOW_STOCK,
                message=f"Low stock alert: {label} has only {count} available unit(s). Please create a blood request."
            )

        else:
            level = "Medium"
            message = "Stock is moderate."
            css_class = "medium"

        inventory_summary.append({
            "blood_type": label,
            "count": count,
            "level": level,
            "message": message,
            "css_class": css_class,
         })
    appointments = HospitalAppointment.objects.filter(
    hospital=hp
    ).select_related(
      "donor",
      "blood_request"
    ).order_by("-created_at")
    patient_requests = BloodRequest.objects.filter(
         hospital=hp,
         requested_by=BloodRequest.RequestBy.PATIENT,
         target_donor__isnull=True
        ).order_by("-created_at")[:5]

    return render(request, "hospitals/hospital_dashboard.html", {
        "hp": hp,
        "units": units,
        "requests": requests,
        "patient_requests": patient_requests,
        "alerts": alerts,
        "stats": stats,
        "inventory_summary": inventory_summary,
        "appointments":appointments ,
        "active_tab": "hospital_dashboard"
    })
        
    
# =========================
# PROFILE
# =========================
@login_required
def hospital_profile(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    return render(request, "hospitals/hospital_profile.html", {
        "hp": hp,
        "active_tab": "hospital_profile"
  })


# =========================
# EDIT PROFILE
# =========================
@login_required
def hospital_edit_profile(request):
    hp = _get_hospital_profile(request.user)

    if not hp:
        raise Http404("Not a hospital account")

    if request.method == "POST":

        form = HospitalProfileForm(
            request.POST,
            request.FILES,
            instance=hp
        )

        if form.is_valid():

            hospital_profile = form.save(commit=False)

            hospital_profile.latitude = request.POST.get("latitude") or None
            hospital_profile.longitude = request.POST.get("longitude") or None

            hospital_profile.city = request.POST.get("city")
            hospital_profile.address = request.POST.get("address")

            # remove license
            if form.cleaned_data.get("remove_license"):

                if hospital_profile.license_file:
                    hospital_profile.license_file.delete(save=False)

                hospital_profile.license_file = None

            # remove docs
            if form.cleaned_data.get("remove_docs"):

                if hospital_profile.official_docs:
                    hospital_profile.official_docs.delete(save=False)

                hospital_profile.official_docs = None

            hospital_profile.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("hospital_profile")

        else:

            print(form.errors)

    else:

        form = HospitalProfileForm(instance=hp)

    return render(
        request,
        "hospitals/hospital_edit_profile.html",
        {
            "form": form,
            "hp": hp,
            "active_tab": "hospital_edit_profile"
        }
    )
from django.http import JsonResponse

@login_required
def remove_license(request):
    hp = _get_hospital_profile(request.user)

    if hp and hp.license_file:
        hp.license_file.delete(save=False)
        hp.license_file = None
        hp.save()

    return redirect("hospital_edit_profile")


@login_required
def remove_docs(request):
    hp = _get_hospital_profile(request.user)

    if hp and hp.official_docs:
        hp.official_docs.delete(save=False)
        hp.official_docs = None
        hp.save()

    return redirect("hospital_edit_profile")
# =========================
# INVENTORY LIST
# =========================
@login_required
def inventory_list(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    blood_type = request.GET.get("blood_type", "")
    status     = request.GET.get("status", "")

    # ── all units for this hospital (for stats) ───────────────────────
    all_units = BloodUnit.objects.filter(hospital=hp)

    # ── filtered queryset for the table ──────────────────────────────
    qs = all_units.order_by("expiry_date")
    if blood_type:
        qs = qs.filter(blood_type=blood_type)
    if status:
        qs = qs.filter(status=status)

    # ── same stats as inventory_reports ──────────────────────────────
    total_units     = all_units.count()
    available_units = all_units.filter(status=BloodUnit.Status.AVAILABLE).count()
    expired_units   = all_units.filter(status=BloodUnit.Status.EXPIRED).count()
    discarded_units = all_units.filter(status=BloodUnit.Status.DISCARDED).count()
    reserved_units  = all_units.filter(status=BloodUnit.Status.RESERVED).count()
    collected_units = all_units.filter(status=BloodUnit.Status.COLLECTED).count()
    tested_units    = all_units.filter(status=BloodUnit.Status.TESTED).count()

    low_stock_count   = 0
    out_of_stock_count = 0
    low_stock_types   = []

    for value, label in BLOOD_TYPES:
        count = all_units.filter(
            blood_type=value,
            status=BloodUnit.Status.AVAILABLE
        ).count()
        if count == 0:
            out_of_stock_count += 1
        elif count < 5:
            low_stock_count += 1
            low_stock_types.append({"blood_type": label, "count": count})

    return render(request, "hospitals/inventory_list.html", {
        "hp":               hp,
        "units":            qs,
        "blood_types":      BLOOD_TYPES,
        "statuses":         BloodUnit.Status.choices,
        "active_tab":       "hospital_inventory",

        # ── report stats (same as inventory_reports) ──
        "total_units":      total_units,
        "available_units":  available_units,
        "expired_units":    expired_units,
        "discarded_units":  discarded_units,
        "reserved_units":   reserved_units,
        "collected_units":  collected_units,
        "tested_units":     tested_units,
        "low_stock_count":  low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "low_stock_types":  low_stock_types,
    })

 


# =========================
# ADD UNIT
# =========================
@login_required
def inventory_add(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    if request.method == "POST":
        form = BloodUnitForm(request.POST)

        if form.is_valid():
            unit = form.save(commit=False)
            unit.hospital = hp
            unit.scource="Manual"

            if unit.expiry_date and unit.expiry_date < timezone.localdate():
                unit.status = BloodUnit.Status.EXPIRED

            unit.save()

            messages.success(request, "Blood unit added.")
            return redirect("hospital_inventory")
    else:
        form = BloodUnitForm()

    return render(request, "hospitals/inventory_add.html", {
        "form": form,
        "hp": hp,
        "active_tab": "inevtory_add"
    })


# =========================
# UPDATE STATUS
# =========================
from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BloodUnit

@login_required
def inventory_update_status(request, pk):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    unit = get_object_or_404(BloodUnit, pk=pk, hospital=hp)

    if request.method == "POST":
        new_status = request.POST.get("status")

        valid_statuses = [choice[0] for choice in BloodUnit.Status.choices]

        if new_status in valid_statuses:
            unit.status = new_status
            unit.save()
            messages.success(request, "Status updated successfully.")

        return redirect("hospital_inventory")

    return render(request, "hospitals/inventory_update_status.html", {
        "hp": hp,
        "unit": unit,
        "statuses": BloodUnit.Status.choices,
        "active_tab": "hospital_inventory"
    })

# =========================
# DISCARD UNIT
# =========================
from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BloodUnit

@login_required
def inventory_discard(request, pk):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    unit = get_object_or_404(BloodUnit, pk=pk, hospital=hp)

    if request.method == "POST":
        unit.status = BloodUnit.Status.DISCARDED
        unit.save()
        messages.success(request, "Blood unit discarded successfully.")
        return redirect("hospital_inventory")

    return render(request, "hospitals/inventory_discard_confirm.html", {
        "hp": hp,
        "unit": unit,
        "active_tab": "hospital_inventory"
    })
# =========================
# AVAILABLE DONORS
# =========================
@login_required
def available_donors(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    blood_type = request.GET.get("blood_type", "")
    city = request.GET.get("city", "")

    donors = DonorProfile.objects.filter(
        is_available=True
    ).exclude(
        blood_type__isnull=True
    )

    if blood_type:
        donors = donors.filter(blood_type=blood_type)

    if city:
        donors = donors.filter(city__icontains=city)

    donor_list = []

    for donor in donors:
        distance = calculate_distance_km(
            hp.latitude,
            hp.longitude,
            donor.latitude,
            donor.longitude
        )

        donor.distance_km = distance
        donor_list.append(donor)

    donor_list.sort(
        key=lambda d: d.distance_km if d.distance_km is not None else 999999
    )

    return render(request, "hospitals/available_donors.html", {
        "hp": hp,
        "donors": donor_list,
        "blood_types": BLOOD_TYPES,
        "active_tab": "available_donors"
    })

# =========================
# BLOOD REQUEST LIST
# =========================
@login_required
def blood_request_list(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    requests = BloodRequest.objects.filter(
        hospital=hp
    ).order_by("-created_at")

    return render(request, "hospitals/blood_request_list.html", {
        "hp": hp,
        "requests": requests,
        "active_tab": "blood_request_list"
    })





# =========================
# CREATE BLOOD REQUEST
# =========================
@login_required
def blood_request_create(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    if request.method == "POST":
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.hospital = hp
            req.requested_by = BloodRequest.RequestBy.HOSPITAL
            req.save()

            Alert.objects.create(
                hospital=hp,
                alert_type=Alert.AlertType.NEW_REQUEST,
                message=f"New request for {req.blood_type}"
            )

            messages.success(request, "Request created.")
            return redirect("hospital_requests")
    else:
        form = BloodRequestForm()

    return render(request, "hospitals/blood_request_create.html", {
        "form": form,
        "hp": hp,
        "active_tab": "blood_request_create"

    })
# =========================
# BLOOD REQUEST LIST + CREATE IN SAME PAGE
# =========================
@login_required
def blood_request_list(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    if request.method == "POST":
        form = BloodRequestForm(request.POST)

        if form.is_valid():
            req = form.save(commit=False)
            req.hospital = hp
            req.requested_by = BloodRequest.RequestBy.HOSPITAL
            req.city = request.POST.get("city") or hp.city
            req.hospital_address = request.POST.get("hospital_address") or hp.address
            req.patient_name = request.POST.get("patient_name") or hp.hospital_name
            req.status = BloodRequest.Status.PENDING
            req.save()

            messages.success(request, "Blood request created successfully.")
            return redirect("hospital_requests")
    else:
        form = BloodRequestForm()

    requests = BloodRequest.objects.filter(
        hospital=hp
    ).order_by("-created_at")

    return render(request, "hospitals/blood_request_list.html", {
        "hp": hp,
        "form": form,
        "requests": requests,
        "active_tab": "blood_request_list"
    })

# =========================
# CANCEL BLOOD REQUEST
# =========================
@login_required
def blood_request_cancel(request, pk):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    req = get_object_or_404(BloodRequest, pk=pk, hospital=hp)

    if request.method == "POST":
        req.status = BloodRequest.Status.CANCELLED
        req.save()
        messages.success(request, "Blood request cancelled successfully.")

    return redirect("hospital_requests")


# =========================
# ALERTS
# =========================
@login_required
def hospital_alerts(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    nearby_donors = []
    has_sound_alert = False

    if hp.latitude and hp.longitude:
        donors = DonorProfile.objects.filter(
            is_available=True,
            latitude__isnull=False,
            longitude__isnull=False
        )

        for donor in donors:
            distance = calculate_distance_km(
                hp.latitude,
                hp.longitude,
                donor.latitude,
                donor.longitude
            )

            if distance is not None and distance <= 15:
                donor.distance_km = distance
                nearby_donors.append(donor)

        nearby_donors.sort(key=lambda d: d.distance_km)

        if nearby_donors:
            has_sound_alert = True

    alerts = Alert.objects.filter(hospital=hp).order_by("-created_at")
    Alert.objects.filter(hospital=hp, is_read=False).update(is_read=True)

    return render(request, "hospitals/hospital_alerts.html", {
        "hp": hp,
        "alerts": alerts,
        "nearby_donors": nearby_donors,
        "has_sound_alert": has_sound_alert,
        "active_tab": "hospital_alerts"
    })

# =========================
# SETTINGS
# =========================
@login_required
def hospital_settings(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    return render(request, "hospitals/hospital_settings.html", {
    "hp": hp,
    "active_tab": "hospital_settings"
    })
from django.shortcuts import get_object_or_404




# =========================
# Reports
# =========================
@login_required
def donor_detail(request, donor_id):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    donor = get_object_or_404(DonorProfile, id=donor_id)

    return render(request, "hospitals/donor_detail.html", {
        "donor": donor,
        "active_tab": "hospital_donors"
    })



from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import Http404

from .models import BloodUnit


@login_required
def inventory_reports(request):
    hp = _get_hospital_profile(request.user)
    if not hp:
        raise Http404("Not a hospital account")

    all_units = BloodUnit.objects.filter(hospital=hp)

    # ── overall counts ────────────────────────────────────────────────
    total_units     = all_units.count()
    available_units = all_units.filter(status=BloodUnit.Status.AVAILABLE).count()
    expired_units   = all_units.filter(status=BloodUnit.Status.EXPIRED).count()
    discarded_units = all_units.filter(status=BloodUnit.Status.DISCARDED).count()
    reserved_units  = all_units.filter(status=BloodUnit.Status.RESERVED).count()
    collected_units = all_units.filter(status=BloodUnit.Status.COLLECTED).count()
    tested_units    = all_units.filter(status=BloodUnit.Status.TESTED).count()

    # ── per-blood-type summary (this is what the table needs) ─────────
    # Each entry: { blood_type, units, status_label }
    inventory_summary = []
    low_stock_count = 0
    out_of_stock_count = 0

    for value, label in BLOOD_TYPES:
        count = all_units.filter(
            blood_type=value,
            status=BloodUnit.Status.AVAILABLE
        ).count()

        if count == 0:
            out_of_stock_count += 1
        elif count < 5:
            low_stock_count += 1

        inventory_summary.append({
            "blood_type": label,
            "units":      count,       
        })

    context = {
        "hp":               hp,
        "active_tab":       "inventory_reports",

        # stats cards
        "total_units":      total_units,
        "available_units":  available_units,
        "expired_units":    expired_units,
        "discarded_units":  discarded_units,
        "reserved_units":   reserved_units,
        "collected_units":  collected_units,
        "tested_units":     tested_units,
        "low_stock_count":  low_stock_count,
        "out_of_stock_count": out_of_stock_count,

        # table rows — same variable name the template uses
        "inventory":        inventory_summary,
    }

    return render(request, "hospitals/inventory_reports.html", context)
@login_required
def accept_patient_request(request, request_id):
    hp = _get_hospital_profile(request.user)

    blood_request = get_object_or_404(
        BloodRequest,
        id=request_id,
        hospital=hp
    )

    blood_request.status = BloodRequest.Status.ACCEPTED
    blood_request.save()
    if blood_request.patient and blood_request.patient.user:
       pprofile = PatientProfile.objects.filter(user=blood_request.patient.user).first()

       if pprofile:
          PatientAlert.objects.create(
            patient_profile=pprofile,
            title="Request Accepted",
            message=f"Your blood request for {blood_request.blood_type} has been accepted by {hp.hospital_name}."
          )

    Alert.objects.create(
        hospital=hp,
        alert_type="Patient Request Accepted",
        message=f"Your request for {blood_request.blood_type} blood has been accepted by {hp.hospital_name}."
    )

    messages.success(request, "Patient request accepted successfully.")
    return redirect("hospital_dashboard")


@login_required
def reject_patient_request(request, request_id):
    hp = _get_hospital_profile(request.user)

    blood_request = get_object_or_404(
        BloodRequest,
        id=request_id,
        hospital=hp
    )

    blood_request.status = BloodRequest.Status.CANCELLED
    blood_request.save()
    if blood_request.patient and blood_request.patient.user:
       pprofile = PatientProfile.objects.filter(user=blood_request.patient.user).first()

       if pprofile:
          PatientAlert.objects.create(
            patient_profile=pprofile,
            title="Request Rejected",
            message=f"Your blood request for {blood_request.blood_type} has been rejected by {hp.hospital_name}."
          )

    Alert.objects.create(
        hospital=hp,
        alert_type="Patient Request Rejected",
        message=f"Your request for {blood_request.blood_type} blood has been rejected by {hp.hospital_name}."
    )

    messages.warning(request, "Patient request rejected.")
    return redirect("hospital_dashboard")


@login_required
def done_patient_request(request, request_id):
    hp = _get_hospital_profile(request.user)

    blood_request = get_object_or_404(
        BloodRequest,
        id=request_id,
        hospital=hp,
        status=BloodRequest.Status.ACCEPTED
    )

    required_units = blood_request.required_units

    available_units = BloodUnit.objects.filter(
        hospital=hp,
        blood_type=blood_request.blood_type,
        status="AVAILABLE"
    )[:required_units]

    if available_units.count() < required_units:
        messages.error(request, "Not enough available blood units in inventory.")
        return redirect("hospital_dashboard")

    for unit in available_units:
        unit.status = "USED"
        unit.save()

    blood_request.status = "COMPLETED"
    blood_request.save()

    Alert.objects.create(
        hospital=hp,
        alert_type="Blood Received",
        message=f"{required_units} unit(s) of {blood_request.blood_type} blood were given to patient {blood_request.patient_name}."
    )

    messages.success(request, "Request completed and inventory updated.")
    return redirect("hospital_dashboard")



@login_required
def mark_appointment_collected(request, appointment_id):
    hp = _get_hospital_profile(request.user)

    appointment = get_object_or_404(
        HospitalAppointment,
        id=appointment_id,
        hospital=hp
    )

    if request.method == "POST":

        if appointment.status == "COLLECTED":
            messages.info(request, "This donation is already collected.")
            return redirect("hospital_dashboard")

        appointment.status = "COLLECTED"
        appointment.save()

        donor = appointment.donor
        donor.is_available = False
        donor.last_donation_date = date.today()
        donor.save()

        BloodUnit.objects.create(
            hospital=hp,
            unit_id=str(int(timezone.now().timestamp() * 1000)),
            blood_type=appointment.blood_request.blood_type,
            units=1,
            volume_ml=450,
            expiry_date=date.today() + timedelta(days=35),
            source=BloodUnit.Source.DONATION,
            status=BloodUnit.Status.COLLECTED
        )

        Alert.objects.create(
            hospital=hp,
            alert_type="Blood Collected",
            message=(
                f"One blood bag collected from "
                f"{donor.full_name or donor.user.username}. "
                f"Blood type: {appointment.blood_request.blood_type}."
            )
        )

        messages.success(
            request,
            "Blood bag collected and added to inventory."
        )

    return redirect("hospital_dashboard")