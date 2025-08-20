from django.contrib import admin
from .models import Agreement

@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "vendor", "effective_date", "term_months", "notice_days", "auto_renews", "created_at")
    search_fields = ("title", "vendor", "renewal_text")
    list_filter = ("vendor", "auto_renews", "effective_date")
    readonly_fields = ("parsed_fields",)
