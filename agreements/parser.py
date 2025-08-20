import re
from datetime import datetime
from PyPDF2 import PdfReader

MONTHS = "(January|February|March|April|May|June|July|August|September|October|November|December)"

def extract_text(fileobj) -> str:
    reader = PdfReader(fileobj)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    return text

def parse_effective_date(text: str):
    # Try multiple patterns for effective date
    patterns = [
        rf"Effective\s+Date\s*:\s*{MONTHS}\s+\d{{1,2}},\s*\d{{4}}",
        rf"Effective\s+Date\s*:\s*\d{{1,2}}/\d{{1,2}}/\d{{4}}",
        rf"Effective\s+Date\s*:\s*\d{{4}}-\d{{2}}-\d{{2}}",
        rf"Date\s*:\s*{MONTHS}\s+\d{{1,2}},\s*\d{{4}}",
        rf"Start\s+Date\s*:\s*{MONTHS}\s+\d{{1,2}},\s*\d{{4}}",
        rf"Commencement\s+Date\s*:\s*{MONTHS}\s+\d{{1,2}},\s*\d{{4}}",
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            date_str = m.group(0).split(":")[1].strip()
            try:
                if "/" in date_str:
                    return datetime.strptime(date_str, "%m/%d/%Y").date()
                elif "-" in date_str:
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                else:
                    return datetime.strptime(date_str, "%B %d, %Y").date()
            except Exception:
                continue
    
    # Fallback: look for any date pattern
    m2 = re.search(rf"{MONTHS}\s+\d{{1,2}},\s*\d{{4}}", text)
    if m2:
        try:
            return datetime.strptime(m2.group(0), "%B %d, %Y").date()
        except Exception:
            pass
    return None

def parse_term_months(text: str):
    # Try multiple patterns for term length
    patterns = [
        r"(\d{1,2})\s*month",
        r"(\d)\s*year",
        r"Term\s*:\s*(\d{1,2})\s*month",
        r"Duration\s*:\s*(\d{1,2})\s*month",
        r"Contract\s+Term\s*:\s*(\d{1,2})\s*month",
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if "year" in pattern.lower():
                return val * 12
            elif 1 <= val <= 60:  # Reasonable range for months
                return val
    
    # Look for year patterns
    y = re.search(r"(\d)\s*year", text, flags=re.IGNORECASE)
    if y:
        return int(y.group(1)) * 12
    
    return 12  # Default to 12 months

def parse_notice_days(text: str):
    # Try multiple patterns for notice period
    patterns = [
        r"(\d{1,3})\s*day",
        r"Notice\s*:\s*(\d{1,3})\s*day",
        r"Notice\s+Period\s*:\s*(\d{1,3})\s*day",
        r"Termination\s+Notice\s*:\s*(\d{1,3})\s*day",
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 15 <= val <= 365:  # Reasonable range for notice days
                return val
    
    return 90  # Default to 90 days

def parse_vendor(text: str):
    # Try multiple patterns for vendor/company name
    patterns = [
        r"Seller\s*:\s*(.+?)(?:\n|$)",
        r"Vendor\s*:\s*(.+?)(?:\n|$)",
        r"Company\s*:\s*(.+?)(?:\n|$)",
        r"Provider\s*:\s*(.+?)(?:\n|$)",
        r"Supplier\s*:\s*(.+?)(?:\n|$)",
        r"Contractor\s*:\s*(.+?)(?:\n|$)",
        r"Between\s+(.+?)\s+and",
        r"Agreement\s+between\s+(.+?)\s+and",
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            vendor = m.group(1).strip()
            if len(vendor) > 3 and len(vendor) < 100:  # Reasonable length
                return vendor
    
    # Fallback: use first line or first few words
    lines = text.strip().splitlines()
    if lines:
        first_line = lines[0].strip()
        if len(first_line) > 3 and len(first_line) < 100:
            return first_line
    
    return "Unknown Vendor"

def parse_renewal_text(text: str):
    # Try multiple patterns for renewal information
    patterns = [
        r"Renewal\s*:\s*(.+?)(?:\n|$)",
        r"Auto-?renew(al)?\s*:\s*(.+?)(?:\n|$)",
        r"Renewal\s+Terms\s*:\s*(.+?)(?:\n|$)",
        r"Automatic\s+Renewal\s*:\s*(.+?)(?:\n|$)",
    ]
    
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if m:
            for g in reversed(m.groups()):
                if g and len(g.strip()) > 3:
                    return g.strip()
    
    return ""

def parse_pdf(fileobj) -> dict:
    text = extract_text(fileobj)
    eff = parse_effective_date(text)
    term = parse_term_months(text)
    notice = parse_notice_days(text)
    vendor = parse_vendor(text)
    rtext = parse_renewal_text(text)
    
    result = {
        "text": text,
        "effective_date": eff.isoformat() if eff else None,
        "term_months": term,
        "notice_days": notice,
        "vendor": vendor,
        "renewal_text": rtext,
    }
    
    return result
