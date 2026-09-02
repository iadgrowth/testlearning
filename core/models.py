from urllib.parse import urlparse
from django.db import models
from django.contrib.auth.models import User


class Customer(models.Model):
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def clean(self):
        if self.website:
            raw = self.website if '://' in self.website else f'https://{self.website}'
            parsed = urlparse(raw)
            self.website = parsed.netloc.removeprefix('www.').lower()

    def __str__(self):
        return f"{self.name} ({self.website})"


class CustomerPowerlist(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='powerlists')
    powerlist_id = models.IntegerField()
    campaign_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.customer.name} → {self.campaign_name} ({self.powerlist_id})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='users')

    def __str__(self):
        return f"{self.user.username} ({self.customer.name})"


class CallReport(models.Model):
    # Call Performance Data
    call_date = models.DateTimeField()
    duration = models.IntegerField(help_text="Duration in seconds")
    disposition = models.CharField(max_length=100)
    last_dial_outcome = models.CharField(max_length=255, blank=True)
    recording_url = models.URLField(max_length=500, null=True, blank=True)
    attempt_count = models.IntegerField(default=1)
    powerlist_id = models.IntegerField(null=True, blank=True)

    # Contact Identity
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    job_title = models.CharField(max_length=150, blank=True)
    company_name = models.CharField(max_length=255, blank=True)

    # Supplemental Context (from ssData)
    ss_data_raw = models.JSONField(default=dict, blank=True)
    location = models.CharField(max_length=255, blank=True)
    company_domain = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(max_length=500, blank=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=1500, blank=True)
    powerlist_notes = models.CharField(max_length=1500, blank=True)  # NEW FIELD


    def __str__(self):
        return f"{self.company_name} - {self.last_name} ({self.disposition})"

    class Meta:
        ordering = ['-call_date']


class DialAttempt(models.Model):
    # One row per Kixie "startcall" webhook event -- fired the moment a line
    # dials, independent of disposition. call_id is unique so webhook
    # retries (or, during Power Dial multi-line dialing, distinct concurrent
    # lines) can't double-count or collide.
    call_id = models.CharField(max_length=100, unique=True)
    call_date = models.DateTimeField()
    call_type = models.CharField(max_length=20, blank=True)  # "outgoing" / "incoming"
    powerlist_id = models.IntegerField(null=True, blank=True)

    from_number = models.CharField(max_length=20, blank=True)
    to_number = models.CharField(max_length=20, blank=True)
    agent_name = models.CharField(max_length=200, blank=True)
    agent_email = models.EmailField(blank=True)
    agent_user_id = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.call_id} ({self.call_type})"

    class Meta:
        ordering = ['-call_date']