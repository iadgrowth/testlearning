from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import CallReport
import json

def index(request):
    return HttpResponse('Fish and Chips')

def test_response(request):
    return HttpResponse('IAD')

@csrf_exempt
def test_post(request):
    try:
        payload_dict = json.loads(request.body)
        create_report_from_payload(payload_dict)
        return HttpResponse("Received!", status=200)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Server Error", status=500)

def create_report_from_payload(payload):
    data = payload.get('data', {})
    call_details = data.get('callDetails', {})
    
    # Safely navigate to the result block
    contact_details = data.get('powerlistContactDetails', {})
    if contact_details:
        contact_details = contact_details.get('result', {})
    
    # Kixie sends ssData as a JSON string: '{"Location": "NYC"}'
    # We must extract it and then parse that string into a dictionary.
    ss_raw = contact_details.get('ssData', '{}')
    
    if isinstance(ss_raw, str):
        try:
            ss_data = json.loads(ss_raw)
        except (json.JSONDecodeError, TypeError):
            ss_data = {}
    else:
        ss_data = ss_raw if isinstance(ss_raw, dict) else {}

    return CallReport.objects.create(
        call_date=call_details.get('calldate'),
        duration=int(call_details.get('duration', 0) or 0), # Added 'or 0' to handle None
        disposition=call_details.get('disposition'),
        recording_url=call_details.get('recordingurl'),
        note=data.get('note', ''),
        
        powerlist_notes=contact_details.get('nextCallRefresher', ''),
        
        powerlist_id=contact_details.get('powerlistId'),
        phone_number=contact_details.get('phoneNumber'),
        first_name=contact_details.get('firstName'),
        last_name=contact_details.get('lastName'),
        job_title=contact_details.get('title'),
        company_name=contact_details.get('companyName'),
        attempt_count=contact_details.get('attemptCount', 1),
        last_dial_outcome=contact_details.get('lastDialOutcome'),

        # Now ss_data is guaranteed to be a dict
        location=ss_data.get('Location', ''),
        company_domain=ss_data.get('Company Domain', ''),
        linkedin_url=ss_data.get('LinkedIn Profile', '')
    )