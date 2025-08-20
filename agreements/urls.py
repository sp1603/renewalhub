from django.urls import path
from . import views

urlpatterns = [
    path("", views.agreement_list, name="agreement_list"),
    path("upload/", views.upload_agreement, name="upload_agreement"),
    path("upcoming/", views.upcoming_view, name="upcoming"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar.ics", views.global_calendar, name="global_calendar"),
    path("agreements/<int:pk>/", views.agreement_detail, name="agreement_detail"),
    path("agreements/<int:pk>/calendar.ics", views.agreement_calendar, name="agreement_calendar"),
    path("api/upcoming", views.upcoming_api, name="upcoming_api"),
]
