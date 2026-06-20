from datetime import timedelta, date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import DonorProfile, DonorActivity
from .models import DonorProfile
from django.shortcuts import get_object_or_404, redirect
from hospitals.models import BloodRequest
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from hospitals.models import BloodRequest
from hospitals.models import HospitalAppointment
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from hospitals.models import BloodRequest
from donors.models import DonorProfile
from math import radians, sin, cos, sqrt, atan2
from datetime import date 
from hospitals.models import Alert
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from datetime import date ,timedelta
import uuid
from requests_app.models import PatientBloodRequest
from donors.models import DonorProfile
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from requests_app.models import PatientProfile, PatientAlert
from donors.models import DonorProfile
from accounts.models import Patient, HospitalProfile
from hospitals.models import BloodRequest, Alert
from hospitals.models import Alert, BloodUnit, BloodRequest
from hospitals.models import HospitalAppointment

BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

EGYPT_CITIES = [
    ("Cairo", "Cairo"),
    ("Alexandria", "Alexandria"),
    ("Giza", "Giza"),
    ("Shubra El Kheima", "Shubra El Kheima"),
    ("Port Said", "Port Said"),
    ("Suez", "Suez"),
    ("Luxor", "Luxor"),
    ("Aswan", "Aswan"),
    ("Asyut", "Asyut"),
    ("Mansoura", "Mansoura"),
    ("Tanta", "Tanta"),
    ("Zagazig", "Zagazig"),
    ("Ismailia", "Ismailia"),
    ("Faiyum", "Faiyum"),
    ("Damietta", "Damietta"),
    ("Minya", "Minya"),
    ("Beni Suef", "Beni Suef"),
    ("Qena", "Qena"),
    ("Sohag", "Sohag"),
    ("Hurghada", "Hurghada"),
    ("Sharm El Sheikh", "Sharm El Sheikh"),
]

def donor_list(request):

    city = request.GET.get("city")
    blood_type = request.GET.get("blood_type")

    
    donors = DonorProfile.objects.select_related("user").exclude(
        user__patient_profile__isnull=False,
    ).exclude(
        user__hospital_profile__isnull=False,
    ).filter(
        is_available=True,
        user__is_staff=False,
        user__is_superuser=False,
    )

    if blood_type:
        donors = donors.filter(blood_type=blood_type)

    if city:
        donors = donors.filter(city=city)

    # ==================================================
    # Hospitals available based on BloodUnit availability
    # ==================================================
    from hospitals.models import HospitalProfile, BloodUnit

    hospitals_qs = HospitalProfile.objects.all()

    if city:
        hospitals_qs = hospitals_qs.filter(city__icontains=city)

    if blood_type:
        hospitals_qs = hospitals_qs.filter(
            blood_units__status=BloodUnit.Status.AVAILABLE,
            blood_units__blood_type=blood_type,
        ).distinct()
    else:
        hospitals_qs = hospitals_qs.filter(
            blood_units__status=BloodUnit.Status.AVAILABLE
        ).distinct()

    hospitals = hospitals_qs.order_by("hospital_name")

    return render(request, "accounts/find_blood.html", {
        "donors": donors,
        "hospitals": hospitals,
        "selected_city": city,
        "selected_blood": blood_type,
        "blood_types": BLOOD_TYPES,
        "egypt_cities": EGYPT_CITIES,
    })
def _get_profile(user):
    profile, _ = DonorProfile.objects.get_or_create(user=user)
    return profile


@login_required
def donor_dashboard(request):
    profile = _get_profile(request.user)

    
    date_eligible = True

    if profile.last_donation_date:
     diff = (date.today() - profile.last_donation_date).days
     date_eligible = diff >= 90

    final_available = profile.is_available and date_eligible

    next_eligible = None
    if profile.last_donation_date:
        next_eligible = profile.last_donation_date + timedelta(days=90)
    total_donations = DonorActivity.objects.filter(
    donor=profile,
    title="Donation completed"
    ).count()

    stats = {
       "blood_type": profile.blood_type or "—",
       "last_donation": profile.last_donation_date,
       "total_donations": total_donations,
       "next_eligible": next_eligible,
    }

    
    recent_activity = profile.activities.order_by("-created_at")[:5]

    impact_lives = stats["total_donations"] * 3

    return render(request, "donors/donor_dashboard.html", {
        "profile": profile,
        "stats": stats,
        "recent_activity": recent_activity,
        "impact_lives": impact_lives,
        "date_eligible": date_eligible,
        "final_available": final_available,
    })

@login_required
def donor_profile(request):
    profile = _get_profile(request.user)
    return render(request, "donors/donor_profile.html", {"profile": profile})


@login_required
def donor_profile_edit(request):
    profile = _get_profile(request.user)
    

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name", "").strip()
        profile.phone = request.POST.get("phone", "").strip()
        profile.address = request.POST.get("address", "").strip()
        profile.city = request.POST.get("city") or None
        profile.latitude = request.POST.get("latitude") or None
        profile.longitude = request.POST.get("longitude") or None
        
        
        
        profile.blood_type = request.POST.get("blood_type") or None
        profile.medical_conditions = request.POST.get("medical_conditions", "").strip()
        profile.allergies = request.POST.get("allergies", "").strip()

        #  Dates
        dob = request.POST.get("date_of_birth") or ""
        last = request.POST.get("last_donation_date") or ""

        profile.date_of_birth = date.fromisoformat(dob) if dob else None
        profile.last_donation_date = date.fromisoformat(last) if last else None

        #  Weight
        w = request.POST.get("weight_kg") or ""
        profile.weight_kg = int(w) if w else None

        #  أهم جزء (availability auto)
        if profile.last_donation_date:
            diff = (date.today() - profile.last_donation_date).days
            profile.is_available = diff >= 90
        else:
            profile.is_available = True

        # لو أول مرة ومفيش اسم
        if not profile.full_name:
            profile.full_name = request.user.username

        profile.save()
        DonorActivity.objects.create(
         donor=profile,
          title="Profile updated",
         details="Your donor profile information was updated."
        )

        messages.success(request, "Profile updated successfully.")
        return redirect("donor_profile")
        

    return render(request, "donors/profile_edit.html", {
    "profile": profile,
    "EGYPT_CITIES": profile.EGYPT_CITIES,   # 👈 ده المهم
})
    

@login_required
def donor_alerts(request):
    profile = _get_profile(request.user)

    active_requests = BloodRequest.objects.filter(
     target_donor=profile,
     status__in=[
        BloodRequest.Status.PENDING,
        BloodRequest.Status.ACCEPTED
     ]
    ).order_by("-created_at")

    recent_responses = DonorActivity.objects.filter(
        donor=profile,
        title__in=[
            "Blood request accepted",
            "Blood request declined"
        ]
    ).order_by("-created_at")[:5]

    # Mark all as seen - store seen count in session so badge clears
    request.session['donor_seen_requests'] = active_requests.count()

    return render(request, "donors/donor_alerts.html", {
        "profile": profile,
        "active_requests": active_requests,
        "recent_responses": recent_responses,
    })
    

@login_required
def respond_to_request(request, request_id):

    profile = _get_profile(request.user)

    blood_request = BloodRequest.objects.filter(id=request_id).first()

    if not blood_request:
        messages.error(request, "This request no longer exists.")
        return redirect("donor_alerts")

    if request.method == "POST":

        action = request.POST.get("action")

        # Block if donor is not available
        if action == "accept" and not profile.is_available:
            messages.error(request, "⚠️ أنت غير متاح للتبرع الآن. غيّر حالتك لـ Available أولاً من صفحة الـ Availability.")
            return redirect("donor_alerts")

        if blood_request.hospital:
            source_name = blood_request.hospital.hospital_name
        elif blood_request.patient:
            source_name = f"Patient {blood_request.patient.user.username}"
        else:
            source_name = "Unknown source"

        if action == "accept":

            blood_request.status = BloodRequest.Status.ACCEPTED
            blood_request.accepted_at = timezone.now()
            blood_request.save()

            DonorActivity.objects.create(
                donor=profile,
                title="Blood request accepted",
                details=f"You accepted a {blood_request.blood_type} request from {source_name}."
            )

            if blood_request.patient and blood_request.patient.user:
                pprofile = PatientProfile.objects.filter(
                    user=blood_request.patient.user
                ).first()

                if pprofile:
                    PatientAlert.objects.create(
                        patient_profile=pprofile,
                        title="Donor Accepted Your Request",
                        message=f"A donor accepted your request for {blood_request.blood_type} blood."
                    )

            if blood_request.hospital:

                appointment, created = HospitalAppointment.objects.update_or_create(
                    blood_request=blood_request,
                    defaults={
                        "hospital": blood_request.hospital,
                        "donor": profile,
                        "appointment_time": blood_request.scheduled_time or timezone.now(),
                        "status": "CONFIRMED",
                    }
                )

                print("APPOINTMENT SAVED:", appointment.id)

                Alert.objects.create(
                    hospital=blood_request.hospital,
                    alert_type=Alert.AlertType.NEW_REQUEST,
                    message=f"Donor accepted the request for {blood_request.blood_type} blood."
                )

            messages.success(request, "Request accepted successfully.")

        elif action == "decline":

            blood_request.status = BloodRequest.Status.CANCELLED
            blood_request.save()

            DonorActivity.objects.create(
                donor=profile,
                title="Blood request declined",
                details=f"You declined a {blood_request.blood_type} request from {source_name}."
            )

            messages.info(request, "Request declined.")

    return redirect("donor_alerts")


@login_required
def donor_availability_settings(request):
    profile = _get_profile(request.user)

    if request.method == "POST":
        profile.is_available = (request.POST.get("is_available") == "on")

        md = request.POST.get("max_distance_km") or profile.max_distance_km
        profile.max_distance_km = int(md)

        profile.save()

        messages.success(request, "Availability settings saved.")
        return redirect("donor_dashboard")

    return render(request, "donors/donor_settings.html", {"profile": profile})


@login_required
def request_donor(request, donor_id):
    donor = get_object_or_404(DonorProfile, id=donor_id)

    if request.method == "POST":
        scheduled_time = request.POST.get("scheduled_time") or None
        urgency = request.POST.get("urgency", BloodRequest.Urgency.NORMAL)
        blood_type = request.POST.get("blood_type") or donor.blood_type
        required_units = request.POST.get("required_units", 1)

        if not blood_type:
            messages.error(request, "Blood type is required.")
            return redirect("donor_list")

        BloodRequest.objects.create(
            requested_by=BloodRequest.RequestBy.PATIENT,
            patient=request.user.patient_profile if hasattr(request.user, "patient_profile") else None,
            hospital=request.user.hospital_profile if hasattr(request.user, "hospital_profile") else None,
            patient_name=request.user.username,
            blood_type=blood_type,
            required_units=required_units,
            urgency=urgency,
            city=donor.city or "",
            status=BloodRequest.Status.PENDING,
            target_donor=donor,
            scheduled_time=scheduled_time,
            notes=f"Direct request to donor."
        )

        messages.success(request, "Request sent to donor.")
        if hasattr(request.user, "patient_profile"):
          return redirect("patient_dashboard")

        elif hasattr(request.user, "hospital_profile"):
          return redirect("hospital_available_donors")

     
    return redirect("donor_list")

@login_required
def request_hospital(request, hospital_id):
    hospital = get_object_or_404(HospitalProfile, id=hospital_id)

    if request.method == "POST":
        blood_type = request.POST.get("blood_type")
        required_units = request.POST.get("required_units", 1)
        urgency = request.POST.get("urgency", BloodRequest.Urgency.NORMAL)
        scheduled_time = request.POST.get("scheduled_time") or None

        patient_obj = Patient.objects.filter(user=request.user).first()

        blood_request = BloodRequest.objects.create(
            requested_by=BloodRequest.RequestBy.PATIENT,
            patient=patient_obj,
            hospital=hospital,
            patient_name=request.user.username,
            blood_type=blood_type,
            required_units=required_units,
            urgency=urgency,
            city=hospital.city or "",
            hospital_address=hospital.address,
            status=BloodRequest.Status.PENDING,
            scheduled_time=scheduled_time,
            notes="Request sent to hospital from Find Blood."
        )

        Alert.objects.create(
            hospital=hospital,
            alert_type=Alert.AlertType.NEW_REQUEST,
            message=(
                f"New patient request from {blood_request.patient_name} "
                f"for {blood_request.required_units} unit(s) of "
                f"{blood_request.blood_type}."
            )
        )

        messages.success(request, "Request sent to hospital successfully.")
        return redirect("donor_list")

    return redirect("donor_list")

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





@login_required
def donor_nearby_requests(request):
    donor = DonorProfile.objects.get(user=request.user)

    requests = BloodRequest.objects.filter(
        status=BloodRequest.Status.PENDING,
        city=donor.city,
        blood_type=donor.blood_type
    ).order_by("-created_at")

    return render(request, "donors/donor_nearby_requests.html", {
        "requests": requests,
        "donor_city": donor.city,
        "active_tab": "donor_requests"
    })
@login_required
def complete_donation(request, request_id):

    donor = DonorProfile.objects.get(user=request.user)

    # هات أي request بالـ id
    blood_request = BloodRequest.objects.filter(id=request_id).first()

    if not blood_request:
        messages.error(request, "Request not found.")
        return redirect("donor_alerts")

    # لو completed بالفعل
    if blood_request.status == "COMPLETED":
        messages.info(request, "Donation already completed.")
        return redirect("donor_alerts")

    # تحديث الطلب
    blood_request.status = "COMPLETED"
    blood_request.save()

    # donor يبقى unavailable
    donor.is_available = False
    donor.last_donation_date = date.today()
    donor.save()

    # activity لل donor
    DonorActivity.objects.create(
        donor=donor,
        title="Donation completed",
        details=f"You completed donation for {blood_request.blood_type} request."
    )
    if blood_request.patient and blood_request.patient.user:
       pprofile = PatientProfile.objects.filter(user=blood_request.patient.user).first()

       if pprofile:
          PatientAlert.objects.create(
           patient_profile=pprofile,
           title="Donation Completed",
           message=f"Donor {donor.full_name or donor.user.username} completed your {blood_request.blood_type} donation request."
         )

    # =========================
    # لو الطلب من مستشفى
    # =========================
    if blood_request.hospital:

        Alert.objects.create(
            hospital=blood_request.hospital,
            alert_type="Donation Completed",
            message=(
                f"Donor completed donation.\n"
                f"Blood Type: {blood_request.blood_type}"
            )
        )

        # إضافة للمخزون
        BloodUnit.objects.create(
            hospital=blood_request.hospital,
            unit_id=str(int(timezone.now().timestamp() * 1000)),
            blood_type=blood_request.blood_type,
            volume_ml=450,
            expiry_date=date.today() + timedelta(days=35),
            units=getattr(blood_request, "units_needed", 1)or 1,
            source=BloodUnit.Source.DONATION,
            status=BloodUnit.Status.COLLECTED
        )

    # =========================
    # لو الطلب من patient
    # =========================
    patient = getattr(blood_request, "patient", None)

    if patient:
        messages.success(
            request,
            "Donation completed and patient notified."
        )
    else:
        messages.success(
            request,
            "Donation completed successfully."
        )

    return redirect("donor_alerts")