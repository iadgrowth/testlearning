"""
Run with: python manage.py shell < scripts/create_test_user.py
"""

from django.contrib.auth.models import User
from core.models import Customer, CustomerPowerlist, UserProfile

# --- config ---
USERNAME = "davegorman"
PASSWORD = "testpass123"
EMAIL = "dave@capitalbusinessadvisor.com"
CUSTOMER_NAME = "Capital Business Advisors"
CUSTOMER_WEBSITE = "capitalbusinessadvisor.com"
POWERLIST_ID = 361943
CAMPAIGN_NAME = "CBA - Clay List 6/8/26"

# --- teardown existing ---
User.objects.filter(username=USERNAME).delete()
Customer.objects.filter(website=CUSTOMER_WEBSITE).delete()

# --- create ---
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

print(f"Created user: {USERNAME} / {PASSWORD}")
print(f"  Customer:    {customer}")
print(f"  Powerlist:   {POWERLIST_ID} ({CAMPAIGN_NAME})")
print(f"  Profile:     {user.profile}")
