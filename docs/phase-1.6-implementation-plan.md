# Phase 1.6 Implementation Plan: Power Dial Stats Webhook & Tracking

## Current State

| What exists | Status |
|---|---|
| `CallReport` model + webhook (`create_report_from_payload`, `/kixie/test`) | Ready — fires on call disposition |
| Dashboard "Total Dials" KPI | Was `CallReport.objects.count()` — undercounted, since no-answers/busy/voicemail never get a disposition |
| A webhook that fires on every dial attempt, independent of disposition | Did not exist |

Kixie's `startcall` hook event fires the moment a line dials, before any disposition is
known — including every line in a multi-line Power Dial batch. This phase adds a second
webhook + table capturing that event, and repoints "Total Dials" at the real count.

---

## Webhook Payload (`startcall` hook event)

```json
{
  "data": {
    "callDetails": {
      "callid": "d66d15aa-655f-11ea-b174-45f320f374c7",
      "calldate": "2026-06-06T14:21:28.000Z",
      "fromnumber164": "+18666892261",
      "tonumber164": "+14243131560",
      "calltype": "outgoing",
      "fname": "Aldo", "lname": "Barbagiovanni",
      "email": "aldo@kixie.com",
      "userid": 12345,
      "powerlistid": "",
      "cadenceactionprocessid": "",
      "powerlistsessionid": ""
    },
    "hookevent": "startcall"
  }
}
```

Notable quirks this design accounts for:
- `powerlistid` can be an **empty string**, not just absent — normalized to `None`.
- `calltype` distinguishes outgoing vs. inbound — only `"outgoing"` counts as a dial.
- During Power Dial (multi-line) dialing, `startcall` fires once per line, each with its
  own `callid` — confirmed with the account owner, not assumed.

---

## Data Model

**File:** [core/models.py](../core/models.py)

```python
class DialAttempt(models.Model):
    call_id = models.CharField(max_length=100, unique=True)
    call_date = models.DateTimeField()
    call_type = models.CharField(max_length=20, blank=True)
    powerlist_id = models.IntegerField(null=True, blank=True)

    from_number = models.CharField(max_length=20, blank=True)
    to_number = models.CharField(max_length=20, blank=True)
    agent_name = models.CharField(max_length=200, blank=True)
    agent_email = models.EmailField(blank=True)
    agent_user_id = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-call_date']
```

`call_id` is unique so a Kixie webhook retry (or a race between simultaneous multi-line
events) can never double-count — writes use `get_or_create(call_id=...)`, not `create()`.

**Migration:** `core/migrations/0006_dialattempt.py`.

---

## Step 1 — Webhook Ingestion

**File:** [core/views.py](../core/views.py)

Mirrors the existing `create_report_from_payload` / `test_post` pair exactly:

```python
def create_dial_attempt_from_payload(payload):
    data = payload.get('data', {})
    if data.get('hookevent') != 'startcall':
        return None

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
```

---

## Step 2 — URL Wiring

**File:** [core/urls.py](../core/urls.py)

```python
path('kixie/dial-attempt', views.dial_attempt_webhook, name='webhook_dial_attempt'),
```

Full webhook URL to register in Kixie's account settings for the `startcall` hook event
(manual step on Kixie's side, not code — see "Out of Scope"):

```
https://testlearning.onrender.com/kixie/dial-attempt
```

`ALLOWED_HOSTS` in [config/settings.py](../config/settings.py) is driven by the
`DJANGO_ALLOWED_HOSTS` env var — confirmed `testlearning.onrender.com` is already in
there, since the existing `/kixie/test` webhook already works on this same domain. No
`DisallowedHost` risk for the new endpoint (the class of error hit locally testing
against Django's test client during Phase 1.6 smoke testing was a local-only artifact).

---

## Step 3 — Dashboard KPI

**File:** [core/views.py](../core/views.py), `dashboard()` view

```python
dial_qs = DialAttempt.objects.filter(powerlist_id__in=scoped_ids, call_type='outgoing')

kpis = {
    'total_dials': dial_qs.count(),   # was: base_qs.count()
    'conversations': base_qs.filter(disposition__icontains='conversation').count(),
    'meetings': base_qs.filter(disposition__icontains='meeting').count(),
    'info_requests': base_qs.filter(disposition__icontains='information').count(),
}
```

No template changes — `dashboard.html` already renders `{{ kpis.total_dials }}` generically.

---

## Delivery Sequence

| Order | Task | Files touched |
|---|---|---|
| 1 | Add `DialAttempt` model | `core/models.py` |
| 2 | Generate + apply migration | `core/migrations/0006_dialattempt.py` |
| 3 | Add `create_dial_attempt_from_payload` + `dial_attempt_webhook` view | `core/views.py` |
| 4 | Wire new webhook URL | `core/urls.py` |
| 5 | Swap `total_dials` KPI source | `core/views.py` (`dashboard` view) |
| 6 | Smoke test: post the sample payload, confirm one row created, dedupe on retry, `powerlistid: ""` doesn't crash, inbound calls excluded from the KPI | — |

All smoke tests above were run directly against `create_dial_attempt_from_payload` and
the KPI queryset via `manage.py shell` and passed.

---

## Out of Scope for Phase 1.6

- Configuring the actual webhook URL inside Kixie's account settings — manual step on
  Kixie's side.
- Historical backfill of dial attempts that happened before this webhook existed.
- Any UI beyond the single KPI swap (e.g. a dial-attempts detail table, filtering by
  agent) — candidate for a later phase.
