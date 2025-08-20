from __future__ import annotations
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from datetime import date, timedelta, datetime
from calendar import monthcalendar, month_name
from .models import Agreement
from .forms import AgreementForm
from .parser import parse_pdf

@require_http_methods(["GET"])
def agreement_list(request):
    q = request.GET.get("q")
    qs = Agreement.objects.all().order_by("-created_at")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(vendor__icontains=q))
    return render(request, "agreements/list.html", {"agreements": qs})

@require_http_methods(["GET", "POST"])
def upload_agreement(request):
    if request.method == "POST":
        form = AgreementForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            f = request.FILES.get("pdf")
            parsed = parse_pdf(f)
            f.seek(0)
            
            obj.vendor = parsed.get("vendor") or "Unknown Vendor"
            
            effective_date_str = parsed.get("effective_date")
            if effective_date_str:
                try:
                    from datetime import datetime
                    obj.effective_date = datetime.fromisoformat(effective_date_str).date()
                except (ValueError, TypeError):
                    obj.effective_date = None
            else:
                obj.effective_date = None
                
            obj.term_months = parsed.get("term_months") or 12
            obj.notice_days = parsed.get("notice_days") or 90
            obj.parsed_fields = parsed
            obj.renewal_text = parsed.get("renewal_text", "")
            obj.title = parsed.get("vendor") or f"Agreement {obj.vendor}"
            obj.auto_renews = True
            
            obj.save()
            return redirect(obj.get_absolute_url())
    else:
        form = AgreementForm()
    return render(request, "agreements/upload.html", {"form": form})

@require_http_methods(["GET"])
def agreement_detail(request, pk: int):
    obj = get_object_or_404(Agreement, pk=pk)
    events = obj.upcoming_events()
    return render(request, "agreements/detail.html", {"agreement": obj, "events": events})

@require_http_methods(["GET"])
def upcoming_view(request):
    days = int(request.GET.get("days", "365"))
    cutoff = date.today() + timedelta(days=days)
    items = []
    for a in Agreement.objects.all():
        for kind, when, summary, desc in a.upcoming_events():
            if when and when <= cutoff:
                items.append({
                    "agreement": a,
                    "kind": kind,
                    "date": when,
                    "summary": summary,
                    "description": desc,
                })
    items.sort(key=lambda x: x["date"])
    return render(request, "agreements/upcoming.html", {"items": items, "days": days})

@require_http_methods(["GET"])
def calendar_view(request):
    year = int(request.GET.get("year", date.today().year))
    month = int(request.GET.get("month", date.today().month))
    vendor_filter = request.GET.get("vendor", "")
    view_kind = request.GET.get("view", "month")
    
    cal = monthcalendar(year, month)
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    events_by_date = {}
    agreements = Agreement.objects.all()
    if vendor_filter:
        agreements = agreements.filter(vendor__icontains=vendor_filter)
    for a in agreements:
        for kind, when, summary, desc in a.upcoming_events():
            if when and start_date <= when <= end_date:
                events_by_date.setdefault(when, []).append({
                    "agreement": a,
                    "kind": kind,
                    "summary": summary,
                    "description": desc,
                })
    
 
    if view_kind == "week":
        anchor = date.today()
        if anchor.month != month or anchor.year != year:
            anchor = start_date
        weekday = anchor.weekday()  # Mon=0
        week_start = anchor - timedelta(days=weekday)
        week_end = week_start + timedelta(days=6)
        week_dates = [week_start + timedelta(days=i) for i in range(7)]
        week_events = {d: events_by_date.get(d, []) for d in week_dates}
    else:
        week_dates = []
        week_events = {}
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    month_options = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December")
    ]
    current_year = date.today().year
    year_options = [(y, str(y)) for y in range(current_year - 2, current_year + 5)]
    vendor_options = [("", "All Companies")] + [
        (vendor, vendor) for vendor in Agreement.objects.values_list('vendor', flat=True).distinct().order_by('vendor') if vendor
    ]
    
    context = {
        "calendar": cal,
        "year": year,
        "month": month,
        "month_name": month_name[month],
        "events_by_date": events_by_date,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "today": date.today(),
        "month_options": month_options,
        "year_options": year_options,
        "vendor_options": vendor_options,
        "vendor_filter": vendor_filter,
        "view_kind": view_kind,
        "week_dates": week_dates,
        "week_events": week_events,
    }
    
    return render(request, "agreements/calendar.html", context)

@require_http_methods(["GET"])
def global_calendar(request):
    """Generate ICS calendar file for all agreements"""
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AgreementHub//Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    
    for agreement in Agreement.objects.all():
        for kind, when, summary, desc in agreement.upcoming_events():
            if when:
                # Format date for ICS
                dtstart = when.strftime("%Y%m%d")
                uid = f"{agreement.pk}-{kind}-{dtstart}@agreementhub"
                
                ics_content.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uid}",
                    f"DTSTART;VALUE=DATE:{dtstart}",
                    f"SUMMARY:{summary}",
                    f"DESCRIPTION:{desc}",
                    "END:VEVENT",
                ])
    
    ics_content.append("END:VCALENDAR")
    
    response = HttpResponse("\r\n".join(ics_content), content_type="text/calendar")
    response["Content-Disposition"] = 'attachment; filename="agreements.ics"'
    return response

@require_http_methods(["GET"])
def agreement_calendar(request, pk: int):
    """Generate ICS calendar file for a specific agreement"""
    agreement = get_object_or_404(Agreement, pk=pk)
    
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AgreementHub//Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    
    for kind, when, summary, desc in agreement.upcoming_events():
        if when:
            # Format date for ICS
            dtstart = when.strftime("%Y%m%d")
            uid = f"{agreement.pk}-{kind}-{dtstart}@agreementhub"
            
            ics_content.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTART;VALUE=DATE:{dtstart}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{desc}",
                "END:VEVENT",
            ])
    
    ics_content.append("END:VCALENDAR")
    
    response = HttpResponse("\r\n".join(ics_content), content_type="text/calendar")
    response["Content-Disposition"] = f'attachment; filename="{agreement.title.replace(" ", "_")}.ics"'
    return response

@require_http_methods(["GET"])
def upcoming_api(request):
    days = int(request.GET.get("days", "365"))
    cutoff = date.today() + timedelta(days=days)
    payload = []
    for a in Agreement.objects.all():
        for kind, when, summary, desc in a.upcoming_events():
            if when and when <= cutoff:
                payload.append({
                    "agreement_id": a.pk,
                    "title": a.title,
                    "vendor": a.vendor,
                    "kind": kind,
                    "date": when.isoformat(),
                    "summary": summary,
                    "description": desc,
                })
    payload.sort(key=lambda x: x["date"])
    return JsonResponse({"items": payload, "count": len(payload)})
