# Phase 1.5 Implementation Plan: Customer Setup & Administration

## Current State

| What exists | Status |
|---|---|
| `Customer`, `CustomerPowerlist`, `UserProfile` models | Ready |
| Django admin registration for all three models | Ready |
| Dashboard view scoped to logged-in user's customer | Ready |
| Custom admin UI for customer/user management | Does not exist |
| Staff-only access control decorator | Does not exist |

The Django admin at `/admin/` technically works for this, but it exposes all of Django's internals and is not a usable interface to hand off to someone managing client accounts day-to-day. Phase 1.5 builds a purpose-built management section.

---

## Who Can Access This

These screens are internal — not for clients. Access is limited to Django staff users (`user.is_staff = True`).

A `staff_required` decorator wraps every management view:

```python
from django.contrib.auth.decorators import login_required, user_passes_test

staff_required = user_passes_test(lambda u: u.is_staff, login_url='/login/')
```

Clients hit `/dashboard/`. Staff hit `/manage/`. The two sections are fully separate.

---

## URL Structure

```
GET  /manage/                              → Customer list (home screen)
GET  /manage/customer/new/                 → Create customer form
POST /manage/customer/new/                 → Save new customer
GET  /manage/customer/<id>/                → Customer detail (edit + powerlists + users)
POST /manage/customer/<id>/                → Save customer edits
POST /manage/customer/<id>/powerlist/add/  → Add a powerlist to this customer
POST /manage/customer/<id>/powerlist/<pl_id>/delete/  → Remove a powerlist
GET  /manage/customer/<id>/user/new/       → Create user form for this customer
POST /manage/customer/<id>/user/new/       → Save new user
POST /manage/customer/<id>/user/<uid>/reset-password/  → Set a new password
POST /manage/customer/<id>/user/<uid>/delete/          → Delete user account
```

---

## Data Model Changes

No new models required. The existing `Customer`, `CustomerPowerlist`, and `UserProfile` models cover everything.

---

## Step 1 — Forms

**File:** `core/forms.py` (new file)

### `CustomerForm`
```python
from django import forms
from django.contrib.auth.models import User
from .models import Customer, CustomerPowerlist

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'website']
```

The `Customer.clean()` method already normalizes the website field, so no extra logic needed here.

### `CustomerPowerlistForm`
```python
class CustomerPowerlistForm(forms.ModelForm):
    class Meta:
        model = CustomerPowerlist
        fields = ['powerlist_id', 'campaign_name']
```

Used to add a single powerlist entry to a customer. Rendered inline on the customer detail page.

### `UserCreateForm`
```python
class UserCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        if User.objects.filter(username=cleaned.get('username')).exists():
            raise forms.ValidationError("That username is already taken.")
        return cleaned
```

### `PasswordResetForm`
```python
class PasswordResetForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_password') != cleaned.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned
```

---

## Step 2 — Views

**File:** [core/views.py](../core/views.py) (additions only)

### Customer List
```
GET /manage/
```
Query all customers, annotate each with powerlist count, user count, and record count.

```python
from django.db.models import Count

@staff_required
def manage_home(request):
    customers = Customer.objects.annotate(
        powerlist_count=Count('powerlists', distinct=True),
        user_count=Count('users', distinct=True),
    )
    return render(request, 'manage/home.html', {'customers': customers})
```

### Create Customer
```
GET/POST /manage/customer/new/
```
Renders a `CustomerForm`. On POST, calls `form.full_clean()` (which triggers `Customer.clean()` for website normalization) then saves and redirects to the new customer's detail page.

### Customer Detail
```
GET/POST /manage/customer/<id>/
```
The main workhorse view. One page shows:
- Editable customer fields (name, website) via `CustomerForm`
- All attached powerlists with a delete button per row
- An inline "Add Powerlist" form (`CustomerPowerlistForm`)
- All user accounts linked to this customer with a delete and password-reset button per row
- An "Add User" button linking to the user creation form

On POST, handles the customer edit form only. Powerlist and user actions each hit their own POST endpoints (see URL structure above).

### Add / Delete Powerlist
Both are POST-only views. "Add" validates the `CustomerPowerlistForm` and saves. "Delete" looks up the `CustomerPowerlist` by `id` and `customer` (both in the URL) so a staff user can't delete a powerlist belonging to a different customer.

### Create User for Customer
```
GET/POST /manage/customer/<id>/user/new/
```
Validates `UserCreateForm`, creates a `User` with `User.objects.create_user(...)`, then creates a `UserProfile` linking that user to the customer. Redirects back to the customer detail page on success.

### Reset Password
POST-only. Validates `PasswordResetForm`, calls `user.set_password(new_password)` and `user.save()`. The target user must have a `UserProfile` pointing to the customer in the URL — prevents cross-customer actions.

### Delete User
POST-only. Deletes the `User` object (cascade deletes `UserProfile` automatically). Same customer-scoping check as above.

---

## Step 3 — Templates

**New directory:** `core/templates/manage/`

All management templates extend a new `manage/base.html` that adds a nav link back to the customer list.

### `manage/base.html`
Extends `base.html`. Adds a top bar with "Customer Admin" heading and a "← All Customers" link.

### `manage/home.html`
Extends `manage/base.html`.

**Layout:**
- "New Customer" button (top right)
- Table: one row per customer

| Customer Name | Website | Powerlists | Users | Actions |
|---|---|---|---|---|
| Acme Corp | acme.com | 3 | 2 | View → |

Clicking the row (or "View →") goes to `/manage/customer/<id>/`.

### `manage/customer_detail.html`
Extends `manage/base.html`. Three sections on one page:

**Section 1 — Customer Info**
```
[ Customer Name ] [ Website ]  [Save Changes]
```

**Section 2 — Campaigns (Powerlists)**
```
Powerlist ID    Campaign Name              Action
361943          Spring Outreach            [Delete]
412200          Q3 Follow-Up               [Delete]

[ Powerlist ID ] [ Campaign Name ]  [Add Campaign]
```

**Section 3 — User Accounts**
```
Username        Email                      Action
johndoe         john@acme.com              [Reset Password]  [Delete]

[+ Add User]
```

Errors from any form POST are shown inline above the relevant section as a simple red message. Success confirmation is a green flash message using Django's messages framework.

### `manage/user_create.html`
Simple form: username, email, password, confirm password. Submit button, cancel link back to customer detail.

---

## Step 4 — URL Wiring

**File:** [core/urls.py](../core/urls.py)

Add a `manage/` block:

```python
# Management (staff only)
path('manage/', views.manage_home, name='manage_home'),
path('manage/customer/new/', views.manage_customer_new, name='manage_customer_new'),
path('manage/customer/<int:customer_id>/', views.manage_customer_detail, name='manage_customer_detail'),
path('manage/customer/<int:customer_id>/powerlist/add/', views.manage_powerlist_add, name='manage_powerlist_add'),
path('manage/customer/<int:customer_id>/powerlist/<int:pl_id>/delete/', views.manage_powerlist_delete, name='manage_powerlist_delete'),
path('manage/customer/<int:customer_id>/user/new/', views.manage_user_new, name='manage_user_new'),
path('manage/customer/<int:customer_id>/user/<int:user_id>/reset-password/', views.manage_user_reset_password, name='manage_user_reset_password'),
path('manage/customer/<int:customer_id>/user/<int:user_id>/delete/', views.manage_user_delete, name='manage_user_delete'),
```

---

## Step 5 — Onboarding Checklist (Customer Detail Page)

On the customer detail page, show a readiness indicator at the top if the customer is not yet fully set up:

```
⚠ This customer is not ready to log in yet:
  ✗ No campaigns assigned — add at least one Powerlist ID
  ✓ User account exists
```

Logic in the view:

```python
checklist = {
    'has_powerlists': customer.powerlists.exists(),
    'has_users': customer.users.exists(),
}
is_ready = all(checklist.values())
```

The banner only shows if `is_ready` is False. Once both checks pass, no banner.

---

## Delivery Sequence

| Order | Task | Files touched |
|---|---|---|
| 1 | Add `staff_required` decorator | `core/views.py` |
| 2 | Create `core/forms.py` with all four forms | `core/forms.py` (new) |
| 3 | Add all management views | `core/views.py` |
| 4 | Wire URLs | `core/urls.py` |
| 5 | Create `manage/base.html` and `manage/home.html` | `core/templates/manage/` (new dir) |
| 6 | Create `manage/customer_detail.html` | `core/templates/manage/` |
| 7 | Create `manage/user_create.html` | `core/templates/manage/` |
| 8 | Smoke test: log in as staff, create a customer, add a powerlist, create a user, confirm that user can log in and see their dashboard | — |

---

## Out of Scope for Phase 1.5

- Self-service customer registration (customers create their own accounts)
- Role-based permissions beyond staff/non-staff
- Audit log of who made changes
- Email invitation to new users (Phase 2 notification engine)
- Bulk powerlist import from CSV (can be added as a script if needed)
