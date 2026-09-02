from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from core.models import CallReport, Customer, CustomerPowerlist, DialAttempt, UserProfile
from core.forms import CustomerForm, CustomerPowerlistForm, UserCreateForm, PasswordResetForm
import json

staff_required = user_passes_test(lambda u: u.is_staff, login_url='/login/')

def index(request):
    return HttpResponse('Fish and Chips')


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('manage_home')
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
    dial_qs = DialAttempt.objects.filter(powerlist_id__in=scoped_ids, call_type='outgoing')

    # KPIs
    kpis = {
        'total_dials': dial_qs.count(),
        'conversations': base_qs.filter(disposition__icontains='conversation').count(),
        'meetings': base_qs.filter(disposition__icontains='meeting').count(),
        'info_requests': base_qs.filter(disposition__icontains='information').count(),
    }

    # Table rows — default to conversations only, expand with show_all
    show_all = request.GET.get('show_all') == '1'
    if show_all:
        call_records = base_qs
    else:
        call_records = base_qs.filter(disposition__icontains='conversation')

    # Additional filters (applied to table rows only, not KPIs)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    active_outcome = request.GET.get('outcome', '')
    has_notes = request.GET.get('has_notes', '')

    if date_from:
        call_records = call_records.filter(call_date__date__gte=date_from)
    if date_to:
        call_records = call_records.filter(call_date__date__lte=date_to)
    if active_outcome:
        call_records = call_records.filter(disposition__iexact=active_outcome)
    if has_notes == '1':
        call_records = call_records.exclude(powerlist_notes='')

    outcomes = base_qs.values_list('disposition', flat=True).distinct().order_by('disposition')

    return render(request, 'dashboard.html', {
        'kpis': kpis,
        'call_records': call_records,
        'campaigns': campaigns,
        'active_powerlist_id': active_powerlist_id,
        'show_all': show_all,
        'customer': customer,
        'outcomes': outcomes,
        'date_from': date_from,
        'date_to': date_to,
        'active_outcome': active_outcome,
        'has_notes': has_notes,
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

@csrf_exempt
def dial_attempt_webhook(request):
    try:
        payload_dict = json.loads(request.body)
        create_dial_attempt_from_payload(payload_dict)
        return HttpResponse("Received!", status=200)
    except json.JSONDecodeError:
        return HttpResponse("Invalid JSON", status=400)
    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse("Server Error", status=500)

# --- Management views (staff only) ---

@staff_required
def manage_home(request):
    customers = Customer.objects.annotate(
        powerlist_count=Count('powerlists', distinct=True),
        user_count=Count('users', distinct=True),
    )
    return render(request, 'manage/home.html', {'customers': customers})


@staff_required
def manage_customer_new(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.name}' created.")
            return redirect('manage_customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm()
    return render(request, 'manage/customer_new.html', {'form': form})


@staff_required
def manage_customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Customer updated.")
            return redirect('manage_customer_detail', customer_id=customer.id)
    else:
        form = CustomerForm(instance=customer)

    powerlist_form = CustomerPowerlistForm()
    powerlists = customer.powerlists.all()
    users = customer.users.select_related('user').all()
    checklist = {
        'has_powerlists': customer.powerlists.exists(),
        'has_users': customer.users.exists(),
    }
    is_ready = all(checklist.values())

    return render(request, 'manage/customer_detail.html', {
        'customer': customer,
        'form': form,
        'powerlist_form': powerlist_form,
        'powerlists': powerlists,
        'users': users,
        'checklist': checklist,
        'is_ready': is_ready,
    })


@staff_required
def manage_powerlist_add(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        form = CustomerPowerlistForm(request.POST)
        if form.is_valid():
            pid = form.cleaned_data['powerlist_id']
            if customer.powerlists.filter(powerlist_id=pid).exists():
                messages.error(request, f"Powerlist ID {pid} is already assigned to this customer.")
            else:
                pl = form.save(commit=False)
                pl.customer = customer
                pl.save()
                messages.success(request, f"Campaign '{pl.campaign_name}' added.")
        else:
            messages.error(request, "Invalid campaign data — check the fields and try again.")
    return redirect('manage_customer_detail', customer_id=customer_id)


@staff_required
def manage_powerlist_delete(request, customer_id, cp_id):
    customer = get_object_or_404(Customer, id=customer_id)
    cp = get_object_or_404(CustomerPowerlist, id=cp_id, customer=customer)
    if request.method == 'POST':
        name = cp.campaign_name
        cp.delete()
        messages.success(request, f"Campaign '{name}' removed.")
    return redirect('manage_customer_detail', customer_id=customer_id)


@staff_required
def manage_user_new(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data.get('email', ''),
                password=form.cleaned_data['password'],
            )
            UserProfile.objects.create(user=user, customer=customer)
            messages.success(request, f"User '{user.username}' created.")
            return redirect('manage_customer_detail', customer_id=customer_id)
    else:
        form = UserCreateForm()
    return render(request, 'manage/user_create.html', {'form': form, 'customer': customer})


@staff_required
def manage_user_reset_password(request, customer_id, user_id):
    customer = get_object_or_404(Customer, id=customer_id)
    profile = get_object_or_404(UserProfile, user_id=user_id, customer=customer)
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            profile.user.set_password(form.cleaned_data['new_password'])
            profile.user.save()
            messages.success(request, f"Password for '{profile.user.username}' updated.")
        else:
            messages.error(request, "Passwords did not match — try again.")
    return redirect('manage_customer_detail', customer_id=customer_id)


@staff_required
def manage_user_delete(request, customer_id, user_id):
    customer = get_object_or_404(Customer, id=customer_id)
    profile = get_object_or_404(UserProfile, user_id=user_id, customer=customer)
    if request.method == 'POST':
        if profile.user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('manage_customer_detail', customer_id=customer_id)
        username = profile.user.username
        profile.user.delete()
        messages.success(request, f"User '{username}' deleted.")
    return redirect('manage_customer_detail', customer_id=customer_id)


# --- Webhook ---

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


def create_dial_attempt_from_payload(payload):
    data = payload.get('data', {})
    if data.get('hookevent') != 'startcall':
        return None  # ignore other event types if Kixie ever sends them to this URL

    call_details = data.get('callDetails', {})
    raw_pid = call_details.get('powerlistid')
    powerlist_id = int(raw_pid) if raw_pid not in (None, '') else None

    attempt, _ = DialAttempt.objects.get_or_create(
        call_id=call_details.get('callid'),
        defaults=dict(
            call_date=call_details.get('calldate'),
            call_type=call_details.get('calltype', ''),
            powerlist_id=powerlist_id,
            from_number=call_details.get('fromnumber164', ''),
            to_number=call_details.get('tonumber164', ''),
            agent_name=f"{call_details.get('fname', '')} {call_details.get('lname', '')}".strip(),
            agent_email=call_details.get('email', ''),
            agent_user_id=call_details.get('userid'),
        ),
    )
    return attempt