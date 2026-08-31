"""Contact extractor module for parsing candidate contact details using regex and heuristics."""

import re
from typing import Dict, List, Optional, Tuple

EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_REGEX = re.compile(
    r"(?:(?:\+|00)\d{1,3}[\s.-]*)?(?:\(?\d{2,4}\)?[\s.-]*)?\d{3,4}[\s.-]*\d{3,4}(?:[\s.-]*\d{1,4})?|\b\d{10,12}\b"
)

LINKEDIN_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[a-zA-Z0-9_-]+/?",
    re.IGNORECASE
)

GITHUB_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+/?",
    re.IGNORECASE
)

GENERIC_URL_REGEX = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{2,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)",
    re.IGNORECASE
)

HEADER_IGNORE_WORDS = {
    "resume", "curriculum", "vitae", "cv", "page", "email", "phone", "contact",
    "address", "profile", "summary", "experience", "education", "skills",
    "portfolio", "github", "linkedin", "engineer", "developer", "manager",
    "lead", "architect", "analyst", "scientist", "consultant", "student",
    "intern", "software", "frontend", "backend", "fullstack", "full-stack",
    "security", "guard", "officer", "details", "links", "hobbies", "languages",
    "place", "birth", "driving", "license", "full", "male", "female", "married",
    "single", "nationality", "references", "available", "request", "career",
    "objective", "employment", "history", "academic", "background", "qualifications",
    "professional", "interests", "activities", "certifications", "certificates",
    "notable", "projects", "selected", "overview", "statement", "expertise",
    "competencies", "work", "studies", "awards", "honors", "publications"
}


def format_phone(phone_str: Optional[str]) -> Optional[str]:
    """Format raw phone string into a consistent clean format."""
    if not phone_str:
        return None

    digits = re.sub(r"\D", "", phone_str)
    if len(digits) == 10:
        return f"+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    elif len(digits) == 12 and digits.startswith("91"):
        return f"+91 {digits[2:7]} {digits[7:]}"

    return phone_str.strip()


def extract_email(text: str) -> Optional[str]:
    """Extract primary email address from text."""
    matches = EMAIL_REGEX.findall(text)
    if matches:
        return matches[0].strip()
    return None


def extract_phone(text: str) -> Optional[str]:
    """Extract and format primary phone number from text."""
    date_filtered_text = re.sub(r"\b(19|20)\d{2}\s*[-–—]\s*(19|20)\d{2}\b", " ", text)
    date_filtered_text = re.sub(r"\b(19|20)\d{2}\b", " ", date_filtered_text)

    matches = PHONE_REGEX.findall(date_filtered_text)
    for match in matches:
        cleaned_match = match.strip()
        digits = re.sub(r"\D", "", cleaned_match)
        if 9 <= len(digits) <= 15:
            return format_phone(cleaned_match)

    return None


def extract_linkedin(text: str) -> Optional[str]:
    """Extract LinkedIn profile URL."""
    match = LINKEDIN_REGEX.search(text)
    if match:
        url = match.group(0).strip()
        if not url.startswith("http"):
            url = "https://" + url
        return url
    return None


def extract_github_or_portfolio(text: str, linkedin_url: Optional[str] = None) -> Optional[str]:
    """Extract GitHub or portfolio URL."""
    gh_match = GITHUB_REGEX.search(text)
    if gh_match:
        url = gh_match.group(0).strip()
        if not url.startswith("http"):
            url = "https://" + url
        return url

    urls = GENERIC_URL_REGEX.findall(text)
    for url in urls:
        clean_url = url.strip()
        if linkedin_url and clean_url in linkedin_url:
            continue
        if any(domain in clean_url.lower() for domain in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]):
            continue
        return clean_url

    return None


def extract_name_heuristic(text: str) -> Optional[str]:
    """Extract candidate name from header text lines using pattern and linguistic heuristics."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Priority 1: Prominent ALL-CAPS name line (e.g. ROBERT COOPER)
    for line in lines[:10]:
        clean_line = re.sub(r"[,|•·\-_°º]", " ", line).strip()
        words = clean_line.split()
        if 2 <= len(words) <= 4:
            if all(w.isalpha() and w.isupper() for w in words):
                if not any(w.lower() in HEADER_IGNORE_WORDS for w in words):
                    return clean_line.title()

    # Priority 2: Title-Cased name line
    for line in lines[:10]:
        if EMAIL_REGEX.search(line) or PHONE_REGEX.search(line) or "http" in line.lower() or "@" in line or any(c.isdigit() for c in line):
            continue

        clean_line = re.sub(r"[,|•·\-_°º]", " ", line).strip()
        words = clean_line.split()

        if 2 <= len(words) <= 4:
            all_alpha = all(w.replace(".", "").isalpha() for w in words)
            no_ignore_words = not any(w.lower() in HEADER_IGNORE_WORDS for w in words)

            if all_alpha and no_ignore_words:
                if all(w.istitle() or w.isupper() for w in words):
                    return " ".join(words).title()

    return None


def extract_contact_info(text: str, header_text: Optional[str] = None) -> Dict[str, Optional[str]]:
    """Extract standardized contact information dictionary from resume text."""
    search_header = header_text if header_text else text[:600]

    email = extract_email(text)
    phone = extract_phone(text)
    linkedin = extract_linkedin(text)
    portfolio = extract_github_or_portfolio(text, linkedin_url=linkedin)
    name = extract_name_heuristic(search_header)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "portfolio": portfolio
    }
