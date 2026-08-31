"""Skill Matcher module using ontology lookups, exact matching, and RapidFuzz fuzzy matching."""

from collections import defaultdict
import json
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

try:
    from rapidfuzz import fuzz, process
except ImportError:
    fuzz = None
    process = None


DEFAULT_ONTOLOGY_PATH = Path(__file__).resolve().parent.parent / "data" / "skills_ontology.json"

HEADER_IGNORE_WORDS = {
    "skills", "experience", "education", "summary", "projects", "certifications",
    "languages", "hobbies", "awards", "profile", "details", "contact", "about",
    "history", "employment", "academic", "background", "qualifications", "competencies"
}


def _levenshtein_ratio(s1: str, s2: str) -> float:
    """Pure-python Levenshtein similarity ratio between 0.0 and 100.0."""
    if s1 == s2:
        return 100.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    previous_row = list(range(len2 + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1] * (len2 + 1)
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row[j + 1] = min(insertions, deletions, substitutions)
        previous_row = current_row

    dist = previous_row[len2]
    max_len = max(len1, len2)
    return round((1.0 - (dist / max_len)) * 100.0, 2)


def _token_sort_ratio(s1: str, s2: str) -> float:
    """Pure-python Token Sort Ratio similarity matching RapidFuzz behavior."""
    tokens1 = sorted(re.findall(r"\w+", s1.lower()))
    tokens2 = sorted(re.findall(r"\w+", s2.lower()))
    sorted1 = " ".join(tokens1)
    sorted2 = " ".join(tokens2)
    return _levenshtein_ratio(sorted1, sorted2)


class SkillMatcher:
    """Matches resume text against a skills ontology using exact regex and RapidFuzz fuzzy matching."""

    def __init__(self, ontology_path: Optional[Union[str, Path]] = None, fuzzy_threshold: float = 85.0):
        """Initialize SkillMatcher with skills ontology.

        Args:
            ontology_path: Path to skills_ontology.json.
            fuzzy_threshold: RapidFuzz score threshold (0-100) for fuzzy matching. Default 85.0.
        """
        self.ontology_path = Path(ontology_path) if ontology_path else DEFAULT_ONTOLOGY_PATH
        self.fuzzy_threshold = fuzzy_threshold

        self.skills_ontology: List[Dict[str, Any]] = []
        self.alias_to_canonical: Dict[str, str] = {}
        self.canonical_to_category: Dict[str, str] = {}
        self.canonical_skills: Set[str] = set()
        self.exact_patterns: List[Tuple[str, re.Pattern]] = []
        self.alias_by_initial: Dict[str, List[str]] = defaultdict(list)

        self._load_ontology()

    def _load_ontology(self):
        """Load and index skills ontology from JSON file."""
        if not self.ontology_path.exists():
            alt_path = Path("data/skills_ontology.json")
            if alt_path.exists():
                self.ontology_path = alt_path
            else:
                return

        try:
            with open(self.ontology_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.skills_ontology = data.get("skills", [])
        except Exception:
            self.skills_ontology = []

        self._build_indexes()

    def _build_indexes(self):
        """Build fast lookup dictionaries, prefix buckets, categories, and regex patterns."""
        self.alias_to_canonical = {}
        self.canonical_to_category = {}
        self.canonical_skills = set()
        self.exact_patterns = []
        self.alias_by_initial = defaultdict(list)

        for item in self.skills_ontology:
            canonical = item.get("canonical", "")
            category = item.get("category", "Other Competencies")
            if not canonical:
                continue

            self.canonical_skills.add(canonical)
            self.canonical_to_category[canonical] = category

            aliases = item.get("aliases", [canonical])
            if canonical not in aliases:
                aliases.append(canonical)

            for alias in aliases:
                norm_alias = alias.strip().lower()
                if norm_alias:
                    self.alias_to_canonical[norm_alias] = canonical
                    if norm_alias[0].isalnum():
                        self.alias_by_initial[norm_alias[0]].append(norm_alias)

                    escaped_alias = re.escape(alias.strip())
                    if re.match(r"^\w.*\w$", alias.strip()):
                        pattern_str = rf"\b{escaped_alias}\b"
                    elif alias.strip().startswith("."):
                        pattern_str = rf"(?:^|\s){escaped_alias}(?:\s|$|[,;:])"
                    elif alias.strip().endswith(("+", "#")):
                        pattern_str = rf"\b{escaped_alias}(?:\s|$|[,;:])"
                    else:
                        pattern_str = rf"\b{escaped_alias}\b"

                    try:
                        self.exact_patterns.append((canonical, re.compile(pattern_str, re.IGNORECASE)))
                    except re.error:
                        pass

    def extract_skills_from_section_lines(self, skills_section_text: str) -> List[str]:
        """Extract explicit skills listed in the designated Skills section."""
        if not skills_section_text.strip():
            return []

        lines = [line.strip(" -•*|·°º\t") for line in skills_section_text.split("\n") if line.strip(" -•*|·°º\t")]
        extracted: Set[str] = set()

        for line in lines:
            tokens = re.split(r"[,;]+", line)
            for token in tokens:
                clean_tok = token.strip(" -•*|·°º\t")
                if not clean_tok or len(clean_tok) > 60:
                    continue

                norm_tok = clean_tok.lower()
                if norm_tok in self.alias_to_canonical:
                    extracted.add(self.alias_to_canonical[norm_tok])
                else:
                    extracted.add(clean_tok.title())

        return list(extracted)

    def extract_skills(self, text: str, threshold: Optional[float] = None, debug: bool = False) -> List[str]:
        """Extract matching canonical skills from input text using exact and fuzzy matching."""
        if not text or not self.alias_to_canonical:
            return []

        score_thresh = threshold if threshold is not None else self.fuzzy_threshold
        # Enforce reasonable minimum threshold for fuzzy matching
        effective_thresh = max(score_thresh, 85.0)
        found_skills: Set[str] = set()
        debug_logs = []

        # 1. Exact regex patterns from ontology
        for canonical, pattern in self.exact_patterns:
            if canonical not in found_skills:
                m = pattern.search(text)
                if m:
                    found_skills.add(canonical)
                    if debug:
                        debug_logs.append(f"[EXACT] Source: '{m.group(0)}' -> Canonical: '{canonical}' (Score: 100.0)")

        # 2. Candidate phrases
        candidate_phrases = self._extract_candidate_phrases(text)
        all_known_aliases = list(self.alias_to_canonical.keys())

        for phrase in candidate_phrases:
            norm_phrase = phrase.lower().strip()
            if not norm_phrase or norm_phrase in HEADER_IGNORE_WORDS or len(norm_phrase) < 3:
                continue

            # Exact lookup on normalized phrase
            if norm_phrase in self.alias_to_canonical:
                canonical = self.alias_to_canonical[norm_phrase]
                if canonical not in found_skills and debug:
                    debug_logs.append(f"[EXACT PHRASE] Source: '{phrase}' -> Canonical: '{canonical}' (Score: 100.0)")
                found_skills.add(canonical)
                continue

            # Fuzzy matching with token_sort_ratio and length/token guards
            if len(norm_phrase) >= 4 and effective_thresh > 0:
                if process is not None and fuzz is not None:
                    best_match = process.extractOne(
                        norm_phrase,
                        all_known_aliases,
                        scorer=fuzz.token_sort_ratio,
                        score_cutoff=effective_thresh
                    )
                    if best_match:
                        matched_alias, score, _ = best_match
                        p_tokens = norm_phrase.split()
                        a_tokens = matched_alias.split()
                        # Token count and length alignment check to avoid single word subtoken false positives
                        if len(p_tokens) == len(a_tokens) and abs(len(matched_alias) - len(norm_phrase)) <= 3:
                            canonical = self.alias_to_canonical[matched_alias]
                            if canonical not in found_skills and debug:
                                debug_logs.append(f"[FUZZY] Source: '{phrase}' ~ Alias: '{matched_alias}' -> Canonical: '{canonical}' (Score: {score:.1f})")
                            found_skills.add(canonical)
                else:
                    init_char = norm_phrase[0]
                    candidate_aliases = self.alias_by_initial.get(init_char, [])
                    for alias in candidate_aliases:
                        p_tokens = norm_phrase.split()
                        a_tokens = alias.split()
                        if len(p_tokens) == len(a_tokens) and abs(len(alias) - len(norm_phrase)) <= 3:
                            score = _token_sort_ratio(norm_phrase, alias)
                            if score >= effective_thresh:
                                canonical = self.alias_to_canonical[alias]
                                if canonical not in found_skills and debug:
                                    debug_logs.append(f"[FUZZY] Source: '{phrase}' ~ Alias: '{alias}' -> Canonical: '{canonical}' (Score: {score:.1f})")
                                found_skills.add(canonical)
                                break

        if debug:
            for log in debug_logs:
                print(log)

        return sorted(list(found_skills), key=lambda s: s.lower())

    def get_categorized_skills(self, skills_list: List[str]) -> Dict[str, List[str]]:
        """Group a list of skills into clean uppercase category buckets."""
        grouped: Dict[str, List[str]] = defaultdict(list)

        category_map = {
            "Programming Languages": "LANGUAGES",
            "Web & Frontend": "FRAMEWORKS & FRONTEND",
            "Backend Frameworks": "FRAMEWORKS & BACKEND",
            "Databases": "DATABASES & STORAGE",
            "Cloud & DevOps": "CLOUD & DEVOPS",
            "Data Science & AI": "AI & DATA SCIENCE",
            "Big Data": "BIG DATA & ANALYTICS",
            "Data Visualization & BI": "DATA VISUALIZATION",
            "Security & Law Enforcement": "SECURITY & LAW",
            "Security & Defense": "SECURITY & DEFENSE",
            "Security & Operations": "OPERATIONS & COMPLIANCE",
            "Methodologies": "METHODOLOGIES",
            "Testing & QA": "TESTING & QA",
            "Tools & Version Control": "TOOLS & SYSTEMS"
        }

        for skill in skills_list:
            cat = self.canonical_to_category.get(skill, "")
            display_cat = category_map.get(cat, "CORE SKILLS & EXPERTISE")
            grouped[display_cat].append(skill)

        # Sort within each group
        return {k: sorted(v, key=lambda s: s.lower()) for k, v in grouped.items() if v}

    def _extract_candidate_phrases(self, text: str) -> Set[str]:
        """Extract potential 1-gram, 2-gram, and 3-gram skill candidate phrases from text."""
        raw_tokens = re.split(r"[,|\n\t;•·/°º]+", text)
        candidates: Set[str] = set()

        for token in raw_tokens:
            cleaned = token.strip(" -*()[]{}:.,°º\t")
            if not cleaned or len(cleaned) > 50:
                continue

            lower_cleaned = cleaned.lower()
            if lower_cleaned not in HEADER_IGNORE_WORDS:
                candidates.add(cleaned)

            words = cleaned.split()
            if len(words) > 1:
                for w in words:
                    if len(w) >= 2 and w.lower() not in HEADER_IGNORE_WORDS:
                        candidates.add(w)
                for i in range(len(words) - 1):
                    p2 = f"{words[i]} {words[i+1]}"
                    if p2.lower() not in HEADER_IGNORE_WORDS:
                        candidates.add(p2)
                for i in range(len(words) - 2):
                    p3 = f"{words[i]} {words[i+1]} {words[i+2]}"
                    if p3.lower() not in HEADER_IGNORE_WORDS:
                        candidates.add(p3)

        return candidates
