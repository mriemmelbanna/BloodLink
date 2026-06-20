from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from accounts.models import Donor, Patient, HospitalProfile
from requests_app.models import PatientBloodRequest


@staff_member_required
def admin_reports(request):

    total_donors = Donor.objects.count()
    total_patients = Patient.objects.count()
    total_hospitals = HospitalProfile.objects.count()
    total_requests = PatientBloodRequest.objects.count()

    pending_requests = PatientBloodRequest.objects.filter(status='Pending').count()
    completed_requests = PatientBloodRequest.objects.filter(status='Completed').count()

    context = {
        'total_donors': total_donors,
        'total_patients': total_patients,
        'total_hospitals': total_hospitals,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'completed_requests': completed_requests,
    }

    return render(request, 'accounts/admin_reports.html', context)