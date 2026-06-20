from django.shortcuts import render

from accounts.models import Donor, HospitalProfile
from donors.models import DonorActivity
from datetime import timedelta
from hospitals.models import BloodRequest

def home(request):

    registered_donors = Donor.objects.count()

    hospitals_count = HospitalProfile.objects.count()

    total_donations = DonorActivity.objects.filter(
        title="Donation completed"
    ).count()

    lives_saved = total_donations * 3
    requests = BloodRequest.objects.filter(
    accepted_at__isnull=False
    )

    

    context = {
        "registered_donors": registered_donors,
        "hospitals_count": hospitals_count,
        "total_donations": total_donations,
        "lives_saved": lives_saved,
       
    }

    return render(request, "core/home.html", context)
