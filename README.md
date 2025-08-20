# RenewalHub

A tiny Django app to ingest purchase-agreement PDFs and publish a renewal calendar (ICS) with upcoming deadlines.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser  # optional
python manage.py runserver
```

Open: http://127.0.0.1:8000

- **Upload PDFs**: `/upload/`
- **Agreements list**: `/`
- **Upcoming deadlines**: `/upcoming/`
- **Company-wide calendar (ICS)**: `/calendar.ics`
- **Per-agreement ICS**: `/agreements/<id>/calendar.ics`
- **JSON API**: `/api/upcoming?days=365`

## How parsing works
- Extract text with PyPDF2.
- Heuristics scan for:
  - Effective date (e.g., `Effective Date: June 1, 2026`).
  - Term length (months or “year/years”).
  - Notice window (e.g., `90 days`).
  - Renewal clause text (if present).
- If fields are missing, defaults are used: `term_months=12`, `notice_days=90`.
- You can edit parsed fields in the Admin and re-save to regenerate computed dates.

## Environment & Media
- Uploaded files are stored under `MEDIA_ROOT` (defaults to `media/`).
- DEBUG is on by default. For production, configure `SECRET_KEY`, `ALLOWED_HOSTS`, and turn off DEBUG.
