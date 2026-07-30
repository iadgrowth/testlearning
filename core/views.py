from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from core.models import CallReport, CustomerPowerlist
import json

def index(request):
    return HttpResponse('Fish and Chips')


@login_required
def dashboard(request):
    customer = request.user.profile.customer
    campaigns = customer.powerlists.all()
    all_powerlist_ids = list(campaigns.values_list('powerlist_id', flat=True))

    # Campaign filter
    active_powerlist_id = None
    raw_id = request.GET.get('powerlist_id')
    if raw_id and raw_id.isdigit():
        pid = int(raw_id)
        if pid in all_powerlist_ids:
            active_powerlist_id = pid

    scoped_ids = [active_powerlist_id] if active_powerlist_id else all_powerlist_ids
    base_qs = CallReport.objects.filter(powerlist_id__in=scoped_ids)

    # KPIs
    kpis = {
        'total_dials': base_qs.count(),
        'conversations': base_qs.filter(disposition__icontains='conversation').count(),
        'meetings': base_qs.filter(disposition__icontains='meeting').count(),
        'info_requests': base_qs.filter(disposition__icontains='information').count(),
    }

    # Table rows — default to conversations only, expand with ?show_all=1
    show_all = request.GET.get('show_all') == '1'
    if show_all:
        call_records = base_qs
    else:
        call_records = base_qs.filter(disposition__icontains='conversation')

    return render(request, 'dashboard.html', {
        'kpis': kpis,
        'call_records': call_records,
        'campaigns': campaigns,
        'active_powerlist_id': active_powerlist_id,
        'show_all': show_all,
        'customer': customer,
    })

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
        email=contact_details.get('email'),

        # STORE AS JSON OBJECT
        ss_data_raw=ss_raw, 
    )