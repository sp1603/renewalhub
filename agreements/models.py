from __future__ import annotations
from django.db import models
from django.urls import reverse
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

class Agreement(models.Model):
    title = models.CharField(max_length=255)
    vendor = models.CharField(max_length=255, blank=True)
    pdf = models.FileField(upload_to="agreements/")
    effective_date = models.DateField(null=True, blank=True)
    term_months = models.PositiveIntegerField(default=12)
    notice_days = models.PositiveIntegerField(default=90)
    auto_renews = models.BooleanField(default=True)
    renewal_text = models.TextField(blank=True)
    parsed_fields = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or self.vendor or f"Agreement {self.pk}"

    def get_absolute_url(self):
        return reverse("agreement_detail", args=[self.pk])

    def term_end(self) -> date | None:
        if not self.effective_date:
            return None
        return self.effective_date + relativedelta(months=self.term_months) - timedelta(days=1)

    def renewal_date(self) -> date | None:
        if not self.effective_date:
            return None
        return self.effective_date + relativedelta(months=self.term_months)

    def notice_deadline(self) -> date | None:
        te = self.term_end()
        if not te:
            return None
        return te - timedelta(days=self.notice_days)

    def upcoming_events(self):
        events = []
        if self.effective_date:
            events.append(("term_start", self.effective_date,
                           f"Term starts – {self.title} ({self.vendor})",
                           "Agreement term begins today."))
        if self.notice_deadline():
            events.append(("notice_deadline", self.notice_deadline(),
                           f"Notice deadline – {self.title} ({self.vendor})",
                           "Send non-renewal notice by today to avoid auto-renewal."))
        if self.term_end():
            events.append(("term_end", self.term_end(),
                           f"Term ends – {self.title} ({self.vendor})",
                           "End of current term."))
        if self.renewal_date():
            events.append(("renewal_date", self.renewal_date(),
                           f"Renewal date – {self.title} ({self.vendor})",
                           "Auto-renew starts today unless notice given."))
        return events
