# Phase 1 Implementation Plan: Foundation & Mapping

## Current State

| What exists | Status |
|---|---|
| `CallReport` model (`core_callreport`) with `powerlist_id` field | Ready |
| Kixie webhook ingestion at `/kixie/test` | Ready |
| Django auth app installed | Installed, not wired up |
| Dashboard / login UI | Does not exist |
| Customer and mapping models | Do not exist |

---

## Data Model

The ownership hierarchy is:

```
Customer
  ├── many Users (login accounts)
  └── many Powerlist IDs (campaigns)
```

A user never owns powerlist IDs directly. They inherit them through their Customer. When a user logs in, the dashboard queries: *"What is my Customer? What powerlist IDs does that Customer have?"*

---

## Step 1 — New Models

**File:** [core/models.py](../core/models.py)

### `Customer`
Represents a client account (the company you're running calls for).

Two fields are required: company name and website domain. The domain is the unique identifier — no two customers can share the same domain.

```python
from urllib.parse import urlparse

class Customer(models.Model):
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255, unique=True)  # stores bare domain, e.g. acme.com
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        if self.website:
            parsed = urlparse(self.website if '://' in self.website else f'https://{self.website}')
            self.website = parsed.netloc.removeprefix('www.').lower()

    def __str__(self):
        return f"{self.name} ({self.website})"
```

`clean()` normalizes whatever the user types — full URL, with or without `www.`, with or without a scheme — down to the bare domain (`acme.com`). Examples:

| Input | Stored as |
|---|---|
| `https://www.acme.com/about` | `acme.com` |
| `www.acme.com` | `acme.com` |
| `acme.com` | `acme.com` |

The `unique=True` constraint then prevents duplicate entries at the database level.

### `CustomerPowerlist`
Links a Customer to one Powerlist ID. One row per campaign.

```python
class CustomerPowerlist(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='powerlists')
    powerlist_id = models.IntegerField()
    campaign_name = models.CharField(max_length=255)  # human-readable label for the dropdown

    def __str__(self):
        return f"{self.customer.name} → {self.campaign_name} ({self.powerlist_id})"
```

### `UserProfile`
Links a Django `User` to a `Customer`. One user belongs to one customer.

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='users')

    def __str__(self):
        return f"{self.user.username} ({self.customer.name})"
```

Then run `makemigrations` and `migrate`.

**Admin registration:** Register all three models so you can:
- Create a `Customer`
- Attach multiple `CustomerPowerlist` entries to it
- Create a Django `User` and attach a `UserProfile` pointing to that Customer

---

## Step 2 — Authentication

**Goal:** Lock every view behind login. Sessions automatically scope to the user's Customer's powerlist IDs.

### Settings changes (`config/settings.py`)
```python
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'
```

### URL wiring
- `config/urls.py` — include `django.contrib.auth.urls` for `/login/` and `/logout/`
- `core/urls.py` — add `/dashboard/` route

### Template
- `core/templates/registration/login.html` — minimal login form using Django's `AuthenticationForm`

No custom auth logic needed — Django's built-in `LoginView` handles everything.

---

## Step 3 — Dashboard View

**File:** [core/views.py](../core/views.py)

Single `@login_required` view. The access chain on every request:

```
request.user
  → UserProfile.customer
    → CustomerPowerlist.powerlist_id (all of them)
      → core_callreport filtered to those IDs
```

### URL params

```
GET /dashboard/                         → All campaigns, Conversations only
GET /dashboard/?show_all=1              → All campaigns, all dials
GET /dashboard/?powerlist_id=1234       → One campaign, Conversations only
GET /dashboard/?powerlist_id=1234&show_all=1  → One campaign, all dials
```

If a `powerlist_id` is passed that does not belong to the user's Customer, the view ignores it (no 403 needed — just silently falls back to all campaigns).

### KPI queries (on the filtered queryset)

| Card | Filter |
|---|---|
| Total Dials | `count()` of all records |
| Conversations | `disposition__icontains='conversation'` |
| Meetings Booked | `disposition__icontains='meeting'` |
| Information Requests | `disposition__icontains='information'` |

### Context passed to template
`kpis`, `call_records`, `campaigns` (all `CustomerPowerlist` for this customer), `active_powerlist_id`, `show_all`

---

## Step 4 — Dashboard Template

**File:** `core/templates/dashboard.html`

### Layout (top → bottom)
1. **Header bar** — customer name + logout link
2. **KPI cards row** — 4 cards: Total Dials, Conversations, Meetings Booked, Info Requests
3. **Controls row** — Campaign dropdown (left) + "Expand to All Dials" toggle (right)
4. **Conversation log table** — paginated, sorted by date descending

### Table columns
| Date | Contact | Company | Duration | Outcome | Recording |
|---|---|---|---|---|---|

### Audio player
For each row where `recording_url` is not null:
```html
<audio controls preload="none">
  <source src="{{ record.recording_url }}" type="audio/mpeg">
</audio>
```
Use `preload="none"` — do not load audio until the user clicks play.

### All-Dials toggle
A plain link that appends/removes `?show_all=1`. No JavaScript required.

---

## Step 5 — Campaign Selector Dropdown

Populated from the `CustomerPowerlist` records for the logged-in user's Customer. Submits as a GET param.

```html
<select onchange="window.location=this.value">
  <option value="/dashboard/">All Campaigns</option>
  {% for campaign in campaigns %}
    <option value="/dashboard/?powerlist_id={{ campaign.powerlist_id }}"
            {% if campaign.powerlist_id == active_powerlist_id %}selected{% endif %}>
      {{ campaign.campaign_name }}
    </option>
  {% endfor %}
</select>
```

---

## Delivery Sequence

| Order | Task | Files touched |
|---|---|---|
| 1 | Add `Customer`, `CustomerPowerlist`, `UserProfile` models + migrate | `core/models.py`, new migration |
| 2 | Register all three in admin | `core/admin.py` (create) |
| 3 | Wire auth URLs + settings | `config/settings.py`, `config/urls.py` |
| 4 | Create `login.html` | `core/templates/registration/login.html` |
| 5 | Build `dashboard` view | `core/views.py`, `core/urls.py` |
| 6 | Build `dashboard.html` template | `core/templates/dashboard.html` |
| 7 | Smoke test: create Customer, attach powerlist IDs, create User + UserProfile, log in, verify KPIs match DB | — |

---

## Out of Scope for Phase 1

- Commenting system (Phase 2)
- Email notifications (Phase 2)
- Status tags (Phase 2)
- Advanced filtering, charts, mobile polish (Phase 3)
