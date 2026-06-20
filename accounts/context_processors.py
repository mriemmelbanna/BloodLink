from hospitals.models import Alert
from requests_app.models import PatientAlert
from hospitals.models import BloodRequest


def notification_count(request):
    if not request.user.is_authenticated:
        return {'notification_count': 0}

    user = request.user
    count = 0

    try:
        if hasattr(user, 'hospital_profile'):
            count = Alert.objects.filter(
                hospital=user.hospital_profile,
                is_read=False
            ).count()

        elif hasattr(user, 'patient_profile'):
            patient_profile = getattr(user, 'patientprofile', None)
            if patient_profile:
                count = PatientAlert.objects.filter(
                    patient_profile=patient_profile,
                    is_read=False
                ).count()

        elif hasattr(user, 'donor_profile'):
            donor_profile = getattr(user, 'donorprofile', None)
            if donor_profile:
                total = BloodRequest.objects.filter(
                    target_donor=donor_profile,
                    status=BloodRequest.Status.PENDING
                ).count()
                # Badge disappears after visiting alerts page
                seen = request.session.get('donor_seen_requests', 0)
                count = max(0, total - seen)
    except Exception:
        count = 0

    return {'notification_count': count}