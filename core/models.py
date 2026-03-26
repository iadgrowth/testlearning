from django.db import models

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
    location = models.CharField(max_length=255, blank=True)
    company_domain = models.CharField(max_length=255, blank=True)
    linkedin_url = models.URLField(max_length=500, blank=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=1500, blank=True)


    def __str__(self):
        return f"{self.company_name} - {self.last_name} ({self.disposition})"

    class Meta:
        ordering = ['-call_date']