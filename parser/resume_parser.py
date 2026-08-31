"""Resume Parser ATS Engine orchestrator module."""

import json
from pathlib import Path
import re
from typing import Any, BinaryIO, Dict, List, Optional, Union

from .cleaner import clean_text
from .contact_extractor import extract_contact_info
from .extractor import extract_text, UnsupportedFormatError
from .ner_extractor import NERExtractor
from .segmenter import segment_resume
from .skill_matcher import SkillMatcher


class ResumeParser:
    """End-to-end Resume Parser ATS Engine.

    Coordinates text extraction, normalization, section segmentation,
    contact info parsing, named entity recognition, skill matching,
    and auxiliary sections (certifications, languages, hobbies).
    """

    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        ontology_path: Optional[Union[str, Path]] = None,
        skill_fuzzy_threshold: float = 85.0
    ):
        """Initialize the parser components.

        Args:
            spacy_model: Name of the spaCy language model.
            ontology_path: Path to the skills ontology JSON file.
            skill_fuzzy_threshold: RapidFuzz matching threshold for skill extraction.
        """
        self.skill_fuzzy_threshold = skill_fuzzy_threshold
        self.ner_extractor = NERExtractor(model_name=spacy_model)
        self.skill_matcher = SkillMatcher(
            ontology_path=ontology_path,
            fuzzy_threshold=skill_fuzzy_threshold
        )

    def parse_file(
        self,
        file_source: Union[str, Path, BinaryIO, bytes],
        file_name: str = "",
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Parse a resume file (PDF or DOCX) into standardized ATS JSON data.

        Args:
            file_source: File path, file-like binary stream, or bytes.
            file_name: Optional file name to assist format detection when passing stream.
            threshold: Optional override for fuzzy matching threshold.

        Returns:
            Dictionary matching the standardized ATS JSON schema.
        """
        raw_text = extract_text(file_source, file_name=file_name)

        if not raw_text or not raw_text.strip():
            raise ValueError("Extracted resume content is empty or unreadable.")

        return self.parse_text(raw_text, threshold=threshold)

    def parse_text(self, raw_text: str, threshold: Optional[float] = None) -> Dict[str, Any]:
        """Parse raw resume text through the full NLP/ATS pipeline.

        Args:
            raw_text: Raw string content of the resume.
            threshold: Optional override for skill fuzzy threshold.

        Returns:
            Nested dictionary adhering to the standard ATS JSON structure.
        """
        fuzzy_thresh = threshold if threshold is not None else self.skill_fuzzy_threshold

        # 1. Clean and normalize text
        cleaned_text = clean_text(raw_text)

        # 2. Split into semantic sections
        sections = segment_resume(cleaned_text)

        # 3. Extract Contact Details (scoped strictly to contact section or clean header)
        contact_section = sections.get("contact", "").strip()
        contact_header_text = contact_section if contact_section else cleaned_text[:600]

        contact_info = extract_contact_info(
            text=cleaned_text,
            header_text=contact_header_text
        )

        # Refine candidate name using spaCy NER if heuristic didn't find one
        if not contact_info.get("name"):
            ner_name = self.ner_extractor.extract_name_from_doc(contact_header_text)
            if ner_name:
                contact_info["name"] = ner_name

        contact = {
            "name": contact_info.get("name") or "",
            "email": contact_info.get("email") or "",
            "phone": contact_info.get("phone") or "",
            "linkedin": contact_info.get("linkedin") or "",
            "portfolio": contact_info.get("portfolio") or ""
        }

        # 4. Extract Summary
        summary = sections.get("summary", "")

        # 5. Extract Experience
        experience_text = sections.get("experience", "")
        experience = self.ner_extractor.extract_experience(experience_text)

        # 6. Extract Education
        education_text = sections.get("education", "")
        education = self.ner_extractor.extract_education(education_text)

        # 7. Extract Skills
        skills_section_text = sections.get("skills", "")
        extracted_skills = set()

        if skills_section_text:
            explicit_skills = self.skill_matcher.extract_skills_from_section_lines(skills_section_text)
            extracted_skills.update(explicit_skills)

        ontology_skills = self.skill_matcher.extract_skills(cleaned_text, threshold=fuzzy_thresh)
        extracted_skills.update(ontology_skills)

        skills = sorted(list(extracted_skills), key=lambda s: s.lower())

        # 8. Extract Projects
        projects_text = sections.get("projects", "")
        projects = self.ner_extractor.extract_projects(projects_text)

        # 9. Extract Certifications
        certifications_text = sections.get("certifications", "")
        certifications = self._extract_certifications(certifications_text)

        # 10. Extract Languages
        languages_text = sections.get("languages", "")
        languages = self._extract_list_items(languages_text)

        # 11. Extract Hobbies & Interests
        hobbies_text = sections.get("hobbies", "")
        hobbies = self._extract_list_items(hobbies_text)

        return {
            "contact": contact,
            "summary": summary,
            "experience": experience,
            "education": education,
            "skills": skills,
            "projects": projects,
            "certifications": certifications,
            "languages": languages,
            "hobbies": hobbies
        }

    def _extract_list_items(self, text: str) -> List[str]:
        """Extract individual list items from delimited text (commas, newlines, bullets, slashes)."""
        if not text.strip():
            return []

        items: List[str] = []
        raw_tokens = re.split(r"[,|\n\t;•·/°º]+", text)
        for token in raw_tokens:
            clean = token.strip(" -*()[]{}:.,°º\t")
            if clean and len(clean) <= 50:
                # Deduplicate preserving order
                if clean not in items:
                    items.append(clean)
        return items

    def _extract_certifications(self, text: str) -> List[Dict[str, str]]:
        """Extract structured certification entries."""
        if not text.strip():
            return []

        entries = []
        lines = [line.strip(" -•*|·°º\t") for line in text.split("\n") if line.strip(" -•*|·°º\t")]
        for line in lines:
            if len(line) > 3:
                entries.append({
                    "name": line,
                    "issuer": "",
                    "dates": ""
                })
        return entries

    def parse_to_json(self, file_source: Union[str, Path, BinaryIO, bytes], indent: int = 2) -> str:
        """Parse a resume file and return serialized JSON string."""
        result = self.parse_file(file_source)
        return json.dumps(result, indent=indent, ensure_ascii=False)
