# Phase 1 Architecture: Client Call Metrics Portal

---

## System Overview

```
                        ┌─────────────────────────────┐
                        │         Kixie               │
                        │  (Webhook POST on every call)│
                        └──────────────┬──────────────┘
                                       │ POST /kixie/test
                                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Django Application                        │
│                                                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────────┐  │
│  │  Auth Layer │    │  Dashboard   │    │  Webhook Ingestion │  │
│  │  /login     │    │  /dashboard  │    │  /kixie/test       │  │
│  │  /logout    │    │  (view)      │    │  (view)            │  │
│  └──────┬──────┘    └──────┬───────┘    └────────┬───────────┘  │
│         │                  │                     │               │
│         ▼                  ▼                     ▼               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     PostgreSQL                           │   │
│  │                                                          │   │
│  │  auth_user          core_customer    core_userpro file   │   │
│  │  core_customerpow   erlist           core_callreport     │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                                       ▲
                        ┌──────────────┴──────────────┐
                        │         Browser             │
                        │  Client logs in, views      │
                        │  dashboard, plays recordings │
                        └─────────────────────────────┘
```

---

## Database Schema

### Relationships at a glance

```
auth_user ──(OneToOne)──► core_userprofile ──(ForeignKey)──► core_customer
                                                                    │
                                          (ForeignKey, cascade) ◄──┤
                                                                    │
                                          core_customerpowerlist ◄──┘
                                              │
                                              │ powerlist_id (integer, not FK)
                                              │
                                              ▼
                                         core_callreport
                                         (read-only source of truth)
```

### `auth_user` (Django built-in)

| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| username | varchar | login credential |
| password | varchar | hashed |
| first_name | varchar | |
| last_name | varchar | |
| email | varchar | |

### `core_customer`

| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| name | varchar(255) | required |
| website | varchar(255) | required, **unique** — bare domain e.g. `acme.com` |
| created_at | timestamptz | auto |

The `website` field is the business-level unique identifier. The model's `clean()` method normalizes any pasted URL down to the bare domain before saving.

### `core_customerpowerlist`

| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| customer_id | integer FK → core_customer | CASCADE on delete |
| powerlist_id | integer | Kixie Powerlist ID |
| campaign_name | varchar(255) | human-readable label for dropdown |

One row per campaign. A customer with three campaigns has three rows here.

### `core_userprofile`

| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| user_id | integer FK → auth_user | OneToOne, CASCADE on delete |
| customer_id | integer FK → core_customer | CASCADE on delete |

The join table between Django users and customers. A user belongs to exactly one customer and inherits all of that customer's powerlist IDs.

### `core_callreport` (existing, read-only)

| Column | Type | Notes |
|---|---|---|
| id | integer PK | |
| powerlist_id | integer | join point to `core_customerpowerlist` |
| call_date | timestamptz | |
| duration | integer | seconds |
| disposition | varchar | e.g. "conversation", "meeting booked" |
| recording_url | varchar | nullable — HTML5 audio source |
| first_name | varchar | |
| last_name | varchar | |
| company_name | varchar | |
| ... | | other Kixie fields |

This table is never written to by the dashboard. It is populated exclusively by the Kixie webhook.

---

## URL Structure

| Method | URL | Handler | Auth |
|---|---|---|---|
| GET/POST | `/login/` | Django `LoginView` | Public |
| GET | `/logout/` | Django `LogoutView` | Required |
| GET | `/dashboard/` | `dashboard_view` | Required |
| GET | `/dashboard/?powerlist_id=X` | `dashboard_view` | Required |
| GET | `/dashboard/?show_all=1` | `dashboard_view` | Required |
| POST | `/kixie/test` | `test_post` (existing) | Public (Kixie) |

---

## Request Lifecycle: Dashboard

```
Browser GET /dashboard/
         │
         ▼
    @login_required
    ─ not logged in → redirect /login/
    ─ logged in ────────────────────────────────────────────────┐
                                                                │
                                                                ▼
                                          1. Load user's Customer via UserProfile
                                          2. Load all CustomerPowerlist for that Customer
                                          3. Read GET params:
                                             - powerlist_id → filter to one campaign
                                             - show_all     → include all dispositions
                                             - (default)    → all campaigns, conversations only
                                          4. Query core_callreport WHERE
                                             powerlist_id IN (user's list)
                                             [AND disposition ILIKE 'conversation']
                                          5. Aggregate KPIs from same queryset
                                          6. Render dashboard.html
                                                                │
                                                                ▼
                                                        Browser renders:
                                                        - KPI cards
                                                        - Campaign dropdown
                                                        - Conversation log table
                                                        - Audio players
```

---

## Request Lifecycle: Webhook Ingestion

```
Kixie POST /kixie/test  (fires after every call)
         │
         ▼
    Parse JSON body
         │
         ▼
    Extract callDetails + powerlistContactDetails
         │
         ▼
    CallReport.objects.create(...)
         │
         ▼
    core_callreport row inserted
    (dashboard picks it up on next page load — no push needed)
```

---

## File Map

```
testlearning/
├── config/
│   ├── settings.py        ← add LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL
│   └── urls.py            ← include django.contrib.auth.urls + core.urls
│
└── core/
    ├── models.py          ← add Customer, CustomerPowerlist, UserProfile
    ├── admin.py           ← register all three new models (create this file)
    ├── views.py           ← add dashboard_view
    ├── urls.py            ← add /dashboard/ route
    └── templates/
        ├── base.html      ← existing (extend for all pages)
        ├── registration/
        │   └── login.html ← new: login form
        └── dashboard.html ← new: KPI cards + table + audio
```

---

## Data Access Rules

| Actor | Can read | Can write |
|---|---|---|
| Logged-in user | `core_callreport` rows where `powerlist_id` is in their Customer's list | Nothing — dashboard is read-only |
| Admin (Django admin) | Everything | `Customer`, `CustomerPowerlist`, `UserProfile`, `auth_user` |
| Kixie webhook | Nothing | `core_callreport` only |

A user can never see another customer's data. The filtering is enforced in the view by scoping every queryset to the powerlist IDs retrieved from `UserProfile → Customer → CustomerPowerlist`.

---

## KPI Definitions

| Card | Query condition on `core_callreport` |
|---|---|
| Total Dials | No filter — count all rows in scope |
| Conversations | `disposition__icontains='conversation'` |
| Meetings Booked | `disposition__icontains='meeting'` |
| Information Requests | `disposition__icontains='information'` |

"In scope" means filtered to the logged-in user's powerlist IDs, and further to the selected campaign if `?powerlist_id=` is set.
