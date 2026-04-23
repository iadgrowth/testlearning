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
    
    contact_details = data.get('powerlistContactDetails', {})
    if contact_details:
        contact_details = contact_details.get('result', {})
    
    # Extract the nested JSON string from Kixie
    ss_raw = contact_details.get('ssData', '{}')
    

    return CallReport.objects.create(
        call_date=call_details.get('calldate'),
        duration=int(call_details.get('duration', 0) or 0),
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

        # STORE AS JSON OBJECT
        ss_data_raw=ss_raw, 
    )