from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

from .forms import DonorRegisterForm, PatientRegisterForm, HospitalRegisterForm, LoginForm
from .models import Donor, Patient, HospitalProfile, BLOOD_TYPES
from donors.models import DonorProfile
from requests_app.models import PatientProfile
from hospitals.models import Alert, BloodRequest


# =========================
# CONTEXT PROCESSORS
# =========================
def base_context(request):
    if not request.user.is_authenticated:
        return {}
    return {
        'is_donor': hasattr(request.user, 'donor_profile'),
        'is_patient': hasattr(request.user, 'patient_profile'),
        'is_hospital': hasattr(request.user, 'hospital_profile'),
    }


def user_type(request):
    if not request.user.is_authenticated:
        return {}
    return {
        "user_type": (
            "donor" if hasattr(request.user, "donor_profile")
            else "patient" if hasattr(request.user, "patient_profile")
            else "hospital" if hasattr(request.user, "hospital_profile")
            else None
        )
    }


# =========================
# REGISTER CHOICE
# =========================
def register_choice(request):
    return render(request, 'accounts/register_choice.html')


# =========================
# REGISTER
# =========================
def donor_register(request):
    if request.method == "POST":
        form = DonorRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Donor account created successfully. Please login.")
            return redirect("login")
    else:
        form = DonorRegisterForm()
    return render(request, "accounts/donor_register.html", {"form": form})


def patient_register(request):
    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Patient.objects.create(
                user=user,
                username=user.username,
                email=user.email,
                phone=form.cleaned_data['phone'],
                blood_type_needed=form.cleaned_data['blood_type_needed'],
                age=form.cleaned_data['age'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                latitude=form.cleaned_data.get("latitude"),
                longitude=form.cleaned_data.get("longitude"),
            )
            PatientProfile.objects.update_or_create(
                user=user,
                defaults={
                    "full_name": user.username,
                    "phone": form.cleaned_data["phone"],
                    "address": form.cleaned_data["address"],
                    "city": form.cleaned_data["city"],
                    "latitude": form.cleaned_data.get("latitude"),
                    "longitude": form.cleaned_data.get("longitude"),
                }
            )
            messages.success(request, "Patient account created successfully. Please login.")
            return redirect('login')
    else:
        form = PatientRegisterForm()
    return render(request, 'accounts/patient_register.html', {'form': form})


def hospital_register(request):
    if request.method == "POST":
        form = HospitalRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = HospitalRegisterForm()
    return render(request, "accounts/hospital_register.html", {"form": form})


# =========================
# LOGIN / LOGOUT
# =========================
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(redirect_user_dashboard(user))
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# =========================
# REDIRECT DASHBOARD
# =========================
def redirect_user_dashboard(user):
    if hasattr(user, 'patient_profile'):
        return 'patient_dashboard'
    elif hasattr(user, 'hospital_profile'):
        return 'hospital_dashboard'
    elif hasattr(user, 'donor_profile'):
        return 'donor_dashboard'
    return 'login'


# =========================
# DASHBOARDS (legacy - now handled by app-specific views)
# =========================
@login_required
def donor_dashboard(request):
    return redirect('donor_dashboard')


@login_required
def patient_dashboard(request):
    return redirect('patient_dashboard')


# =========================
# REQUEST HOSPITAL (from find blood page)
# =========================
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
