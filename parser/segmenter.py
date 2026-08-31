"""Segmenter module for splitting cleaned resume text into standard semantic sections."""

import re
from typing import Dict, List, Optional, Tuple

# Comprehensive section synonyms mapping
SECTION_SYNONYMS: Dict[str, List[str]] = {
    "contact": [
        "details",
        "contact details",
        "personal details",
        "contact info",
        "personal info",
        "contact information",
        "links",
        "social links",
        "social profiles",
        "websites & social links",
    ],
    "summary": [
        "summary",
        "professional summary",
        "executive summary",
        "career summary",
        "profile",
        "professional profile",
        "about",
        "about me",
        "objective",
        "career objective",
        "professional objective",
        "summary of qualifications",
        "overview",
        "personal statement",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "career history",
        "professional background",
        "relevant experience",
        "internships",
        "internship experience",
        "employment",
        "work background",
    ],
    "education": [
        "education",
        "academic background",
        "academic history",
        "educational qualifications",
        "qualifications",
        "academic qualifications",
        "degrees",
        "education and training",
        "studies",
        "courses & education",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core competencies",
        "key skills",
        "skills & expertise",
        "skills and expertise",
        "technologies",
        "tech stack",
        "tools & technologies",
        "technical proficiency",
        "programming skills",
        "areas of expertise",
        "competencies",
        "skills & abilities",
        "professional skills",
    ],
    "projects": [
        "projects",
        "key projects",
        "personal projects",
        "academic projects",
        "technical projects",
        "portfolio projects",
        "notable projects",
        "selected projects",
        "open source projects",
    ],
    "certifications": [
        "certifications",
        "certificates",
        "licenses",
        "professional certifications",
        "licenses & certifications",
        "courses & certifications",
        "accreditations",
    ],
    "languages": [
        "languages",
        "known languages",
        "language proficiency",
        "languages spoken",
    ],
    "hobbies": [
        "hobbies",
        "interests",
        "activities",
        "personal interests",
        "extra-curricular activities",
        "hobbies & interests",
    ],
    "awards": [
        "awards",
        "honors",
        "achievements",
        "awards & achievements",
        "honors and awards",
        "accomplishments",
    ],
    "publications": [
        "publications",
        "research publications",
        "papers",
        "patents",
    ]
}


def is_potential_header(line: str) -> Optional[str]:
    """Determine whether a single text line represents a section header.

    Args:
        line: Single text line.

    Returns:
        Canonical section name if line matches a known section header, otherwise None.
    """
    cleaned = line.strip()
    if not cleaned:
        return None

    if len(cleaned) > 60:
        return None

    # Strip symbols, bullets, circles like ° or •, markdown #, trailing colons
    normalized = re.sub(r"^[\s#*\-_~>|•·°º]+", "", cleaned)
    normalized = re.sub(r"[\s#*\-_~:|•·°º]+$", "", normalized).strip().lower()

    for canonical, synonyms in SECTION_SYNONYMS.items():
        if normalized in synonyms:
            return canonical

    return None


def segment_resume(cleaned_text: str) -> Dict[str, str]:
    """Segment a cleaned resume string into canonical sections.

    The text before the first identified section header (and any explicit 'details'/'links' section)
    is categorized as 'contact' containing personal info, address, phone, and links.

    Args:
        cleaned_text: Normalized resume text.

    Returns:
        Dictionary mapping canonical section keys to section text.
    """
    if not cleaned_text or not isinstance(cleaned_text, str):
        return {
            "contact": "",
            "summary": "",
            "experience": "",
            "education": "",
            "skills": "",
            "projects": "",
            "certifications": "",
            "languages": "",
            "hobbies": "",
            "awards": ""
        }

    lines = cleaned_text.split("\n")
    sections: Dict[str, List[str]] = {
        "contact": [],
        "summary": [],
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certifications": [],
        "languages": [],
        "hobbies": [],
        "awards": []
    }

    current_section = "contact"
    first_header_found = False

    for line in lines:
        detected_section = is_potential_header(line)

        if detected_section:
            first_header_found = True
            current_section = detected_section
            if current_section not in sections:
                sections[current_section] = []
        else:
            if not first_header_found:
                sections["contact"].append(line)
            else:
                sections[current_section].append(line)

    result: Dict[str, str] = {}
    for sec_name, sec_lines in sections.items():
        result[sec_name] = "\n".join(sec_lines).strip()

    return result
