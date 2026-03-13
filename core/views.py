from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from calls.models import CallReport

def index(request):
    print('Index view called')
    return HttpResponse('Fish and Chips')

def test_response(request):
    return HttpResponse('IAD')

@csrf_exempt  # <--- Add this decorator
def test_post(request):
    print('Received POST request with data:', request.body)
    create_report_from_payload(request.body)
    return HttpResponse("Received!", status=200)


def create_report_from_payload(payload):
    data = payload.get('data', {})
    call_details = data.get('callDetails', {})
    contact_details = data.get('powerlistContactDetails', {}).get('result', {})
    ss_data = contact_details.get('ssData', {})

    return CallReport.objects.create(
        # Mapping Call Details
        call_date=call_details.get('calldate'),
        duration=int(call_details.get('duration', 0)),
        disposition=call_details.get('disposition'),
        recording_url=call_details.get('recordingurl'),
        
        # Mapping Contact/Result Details
        powerlist_id=contact_details.get('powerlistId'),
        phone_number=contact_details.get('phoneNumber'),
        first_name=contact_details.get('firstName'),
        last_name=contact_details.get('lastName'),
        job_title=contact_details.get('title'),
        company_name=contact_details.get('companyName'),
        attempt_count=contact_details.get('attemptCount', 1),
        last_dial_outcome=contact_details.get('lastDialOutcome'),

        # Mapping Nested ssData
        location=ss_data.get('Location', ''),
        company_domain=ss_data.get('Company Domain', ''),
        linkedin_url=ss_data.get('LinkedIn Profile', '')
    )