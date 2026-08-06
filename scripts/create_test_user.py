"""
Run with: python manage.py shell < scripts/create_test_user.py
"""

from django.contrib.auth.models import User
from core.models import Customer, CustomerPowerlist, UserProfile

# --- config ---
USERNAME = "testuser"
PASSWORD = "testpass123"
EMAIL = "dave@capitalbusinessadvisor.com"
CUSTOMER_NAME = "Capital Business Advisors"
CUSTOMER_WEBSITE = "capitalbusinessadvisor.com"
POWERLIST_ID = 361943
CAMPAIGN_NAME = "CBA - Clay List 6/8/26"

STAFF_USERNAME = "jwelch"
STAFF_PASSWORD = "testjwelchpass123"
STAFF_EMAIL = "john@iadgrowth.com"

# --- teardown existing ---
User.objects.filter(username=USERNAME).delete()
User.objects.filter(username=STAFF_USERNAME).delete()
Customer.objects.filter(website=CUSTOMER_WEBSITE).delete()

# --- create customer user ---
customer = Customer.objects.create(name=CUSTOMER_NAME, website=CUSTOMER_WEBSITE)

CustomerPowerlist.objects.create(
    customer=customer,
    powerlist_id=POWERLIST_ID,
    campaign_name=CAMPAIGN_NAME,
)

user = User.objects.create_user(
    username=USERNAME,
    email=EMAIL,
    password=PASSWORD,
)

UserProfile.objects.create(user=user, customer=customer)

# --- create staff user ---
staff = User.objects.create_user(
    username=STAFF_USERNAME,
    email=STAFF_EMAIL,
    password=STAFF_PASSWORD,
)
staff.is_staff = True
staff.save()

print(f"Created user:  {USERNAME} / {PASSWORD}")
print(f"  Customer:    {customer}")
print(f"  Powerlist:   {POWERLIST_ID} ({CAMPAIGN_NAME})")
print(f"  Profile:     {user.profile}")
print()
print(f"Created staff: {STAFF_USERNAME} / {STAFF_PASSWORD}")
print(f"  is_staff:    {staff.is_staff}")
