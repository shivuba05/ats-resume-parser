"""NER Extractor module using spaCy en_core_web_sm pipeline and custom EntityRuler."""

import re
from typing import Any, Dict, List, Optional, Tuple

try:
    import spacy
    from spacy.language import Language
    from spacy.pipeline import EntityRuler
except ImportError:
    spacy = None
    Language = None
    EntityRuler = None

# Degree and certificate patterns for custom EntityRuler
DEGREE_PATTERNS = [
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["b.tech", "btech", "b.tech."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["m.tech", "mtech", "m.tech."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["b.e", "be", "b.e."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["m.e", "me", "m.e."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["b.sc", "bsc", "b.sc.", "b.s", "bs", "b.s."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["m.sc", "msc", "m.sc.", "m.s", "ms", "m.s."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["b.a", "ba", "b.a."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["m.a", "ma", "m.a."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["bca", "b.c.a", "b.c.a."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["mca", "m.c.a", "m.c.a."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["bba", "b.b.a", "b.b.a."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["mba", "m.b.a", "m.b.a."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["ph.d", "phd", "ph.d."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["b.com", "bcom", "b.com."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["m.com", "mcom", "m.com."]}}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "bachelor"}, {"LOWER": "of"}, {"OP": "+"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "bachelors"}, {"LOWER": "in"}, {"OP": "+"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "bachelor's"}, {"LOWER": "in"}, {"OP": "+"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "bachelor's"}, {"LOWER": "degree"}, {"OP": "*"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "master"}, {"LOWER": "of"}, {"OP": "+"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "masters"}, {"LOWER": "in"}, {"OP": "+"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "master's"}, {"LOWER": "in"}, {"OP": "+"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "master's"}, {"LOWER": "degree"}, {"OP": "*"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "doctor"}, {"LOWER": "of"}, {"LOWER": "philosophy"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "associate"}, {"LOWER": "degree"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": "diploma"}, {"LOWER": "in"}, {"OP": "+"}]},
    {"label": "DEGREE", "pattern": [{"LOWER": {"IN": ["cpo", "cpop", "socp"]}}]},
]

COLLEGE_KEYWORDS = [
    "university", "institute", "college", "school of", "academy",
    "polytechnic", "campus", "faculty", "iit", "nit", "bits", "mit", "stanford", "harvard",
    "berkeley", "oxford", "cambridge", "foundation", "asis", "training"
]

DEGREE_KEYWORDS = [
    "bachelor", "master", "doctor", "phd", "b.tech", "m.tech", "b.sc", "m.sc", "bba", "mba",
    "program", "programme", "certificate", "certification", "training", "diploma", "associate", "degree", "cpop", "socp", "cpo"
]

MONTH_REGEX = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"

DATE_FULL_RANGE_REGEX = re.compile(
    rf"\b(?:{MONTH_REGEX}\.?,?\s+)?(?:19|20)\d{{2}}\s*(?:[-–—to/]+\s*(?:(?:{MONTH_REGEX}\.?,?\s+)?(?:19|20)\d{{2}}|Present|Current|Now|Till Date))\b",
    re.IGNORECASE
)

DATE_SINGLE_REGEX = re.compile(
    rf"\b(?:{MONTH_REGEX}\.?,?\s+)?(?:19|20)\d{{2}}\b",
    re.IGNORECASE
)

JOB_TITLE_KEYWORDS = [
    "engineer", "developer", "architect", "scientist", "manager", "lead",
    "director", "analyst", "consultant", "designer", "intern", "associate",
    "administrator", "specialist", "officer", "head", "vp", "programmer",
    "founder", "co-founder", "cto", "ceo", "cpo", "owner",
    "guard", "security", "agent", "investigator", "technician", "inspector",
    "coordinator", "assistant", "supervisor", "representative", "practitioner",
    "attendant", "operator", "counselor", "nurse", "teacher", "advisor"
]

CURRICULUM_OR_DESC_REGEX = re.compile(
    r"^(?:[-•*|·°º\t\s]*)(?:course\s*curriculum|curriculum|coursework|courses|relevant\s*courses|major|gpa|grade|thesis|project|description|modules|focus)\b",
    re.IGNORECASE
)


class NERExtractor:
    """Named Entity Recognition & semantic extractor for resume elements."""

    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize spaCy pipeline and attach custom EntityRuler."""
        self.model_name = model_name
        self.nlp = None
        self._load_pipeline(model_name)

    def _load_pipeline(self, model_name: str):
        """Load spaCy model and configure EntityRuler."""
        if spacy is None:
            return

        try:
            self.nlp = spacy.load(model_name)
        except Exception:
            try:
                self.nlp = spacy.blank("en")
            except Exception:
                self.nlp = None
                return

        if self.nlp:
            try:
                if "entity_ruler" in self.nlp.pipe_names:
                    ruler = self.nlp.get_pipe("entity_ruler")
                else:
                    ruler = self.nlp.add_pipe("entity_ruler", before="ner" if "ner" in self.nlp.pipe_names else None)

                ruler.add_patterns(DEGREE_PATTERNS)
            except Exception:
                pass

    def extract_name_from_doc(self, text: str) -> Optional[str]:
        """Extract candidate PERSON name using spaCy NER."""
        if not self.nlp or not text:
            return None

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:8]:
            if any(char.isdigit() for char in line) or "@" in line or "http" in line.lower():
                continue

            clean_line = re.sub(r"[,|•·\-_°º]", " ", line).strip()
            words = clean_line.split()
            if 2 <= len(words) <= 4:
                doc = self.nlp(line)
                for ent in doc.ents:
                    if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                        return ent.text.strip().title()

        return None

    def _split_title_company(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """Split a single line into (title, company) if separated by standard delimiters or multiple spaces/tabs."""
        clean_l = line.strip(" -•*|·°º\t")
        if not clean_l:
            return None, None

        # Check explicit separators
        separator_patterns = [
            r"\s+at\s+",
            r"\s+@\s+",
            r"\s*[-–—|]\s*",
            r"\s{2,}|\t+",
            r"\s*,\s*"
        ]

        for sep_pat in separator_patterns:
            parts = re.split(sep_pat, clean_l, flags=re.IGNORECASE)
            if len(parts) >= 2:
                part1 = parts[0].strip(" -•*|·°º\t,")
                part2 = " ".join([p.strip(" -•*|·°º\t,") for p in parts[1:] if p.strip()]).strip()

                if not part1 or not part2:
                    continue

                # Neither part should be purely a date
                if DATE_FULL_RANGE_REGEX.fullmatch(part1) or DATE_FULL_RANGE_REGEX.fullmatch(part2):
                    continue

                p1_lower = part1.lower()
                p2_lower = part2.lower()

                p1_is_title = any(kw in p1_lower for kw in JOB_TITLE_KEYWORDS)
                p2_is_title = any(kw in p2_lower for kw in JOB_TITLE_KEYWORDS)

                if p1_is_title and not p2_is_title:
                    return part1, part2
                elif p2_is_title and not p1_is_title:
                    return part2, part1
                elif p1_is_title:
                    return part1, part2

        return None, None

    def _split_degree_institution(self, line: str) -> Tuple[Optional[str], Optional[str]]:
        """Split a single line into (degree, institution) if both are present."""
        clean_l = line.strip(" -•*|·°º\t")
        if not clean_l:
            return None, None

        separator_patterns = [
            r"\s*[-–—|]\s*",
            r"\s+at\s+",
            r"\s*,\s*"
        ]

        for sep_pat in separator_patterns:
            parts = re.split(sep_pat, clean_l, flags=re.IGNORECASE)
            if len(parts) >= 2:
                part1 = parts[0].strip(" -•*|·°º\t,")
                part2 = " ".join([p.strip(" -•*|·°º\t,") for p in parts[1:] if p.strip()]).strip()

                if not part1 or not part2:
                    continue

                # Neither part should be purely a date
                if DATE_FULL_RANGE_REGEX.fullmatch(part1) or DATE_FULL_RANGE_REGEX.fullmatch(part2) or DATE_SINGLE_REGEX.fullmatch(part1):
                    continue

                p1_lower = part1.lower()
                p2_lower = part2.lower()

                p1_is_deg = any(kw in p1_lower for kw in DEGREE_KEYWORDS)
                p2_is_inst = any(kw in p2_lower for kw in COLLEGE_KEYWORDS) or (self.nlp and any(ent.label_ == "ORG" for ent in self.nlp(part2).ents))

                if p1_is_deg and p2_is_inst:
                    return part1, part2

                p2_is_deg = any(kw in p2_lower for kw in DEGREE_KEYWORDS)
                p1_is_inst = any(kw in p1_lower for kw in COLLEGE_KEYWORDS)

                if p2_is_deg and p1_is_inst:
                    return part2, part1

                if p1_is_deg and len(part2.split()) <= 8:
                    return part1, part2

        return None, None

    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract structured employment history (company, title, dates, description)."""
        if not text.strip():
            return []

        entries: List[Dict[str, str]] = []
        blocks = self._split_into_entry_blocks(text)

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            title = ""
            company = ""
            dates = ""
            desc_lines = []

            for line in lines:
                # 1. Date line check
                d_match = DATE_FULL_RANGE_REGEX.search(line)
                if d_match and not dates:
                    dates = d_match.group(0).strip()
                    clean_no_date = DATE_FULL_RANGE_REGEX.sub("", line).strip(" -•*|·°º\t,")
                    if not clean_no_date:
                        continue

                # 2. Check if line contains both title and company
                if not title or not company:
                    split_t, split_c = self._split_title_company(line)
                    if split_t and split_c:
                        if not title:
                            title = split_t
                        if not company:
                            company = split_c
                        continue

                lower_line = line.lower()
                clean_line = line.strip(" -•*|·°º\t")

                # 3. Check for standalone title (only non-bullet short lines)
                is_bullet = line.startswith(("-", "•", "*", "·", "°", "º", "—", "–", ">"))
                is_title = any(kw in lower_line for kw in JOB_TITLE_KEYWORDS) and len(clean_line.split()) <= 6
                if is_title and not title and not is_bullet:
                    title = clean_line
                    continue

                # 4. Check for standalone company (via spaCy ORG or known company suffixes)
                if not company and not is_bullet and len(clean_line.split()) <= 6:
                    if self.nlp:
                        doc = self.nlp(line)
                        for ent in doc.ents:
                            if ent.label_ == "ORG" and not company and len(ent.text.split()) <= 5:
                                company = ent.text.strip()
                                break
                    if not company and any(suf in lower_line for suf in ["inc", "corp", "technologies", "solutions", "services", "llc", "ltd", "security"]):
                        company = clean_line
                        continue

                desc_lines.append(line)

            # Fallback for title if still missing (first non-bullet line)
            if not title and lines:
                non_bullet = [l for l in lines if not l.startswith(("-", "•", "*", "·", "°", "º")) and not DATE_FULL_RANGE_REGEX.search(l)]
                if non_bullet:
                    title = non_bullet[0].strip(" -•*|·°º\t")

            # Fallback for company: FAIL CLOSED (empty string). NEVER consume bullet lines or dates as company!
            description = "\n".join(desc_lines).strip()

            if title or company:
                entries.append({
                    "company": company,
                    "title": title,
                    "dates": dates,
                    "description": description
                })

        return entries

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract structured education history (institution, degree, dates)."""
        if not text.strip():
            return []

        entries: List[Dict[str, str]] = []
        blocks = self._split_into_entry_blocks(text)

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            degree = ""
            institution = ""
            dates = ""

            for line in lines:
                # 1. Date extraction
                d_match = DATE_FULL_RANGE_REGEX.search(line) or DATE_SINGLE_REGEX.search(line)
                if d_match and not dates:
                    dates = d_match.group(0).strip()
                    clean_no_date = DATE_FULL_RANGE_REGEX.sub("", line).strip(" -•*|·°º\t,")
                    clean_no_date = DATE_SINGLE_REGEX.sub("", clean_no_date).strip(" -•*|·°º\t,")
                    if not clean_no_date:
                        continue

                # 2. Skip curriculum or bullet lines from being degree or institution
                if CURRICULUM_OR_DESC_REGEX.search(line) or line.startswith(("-", "•", "*", "·", "°", "º")):
                    continue

                lower_line = line.lower()
                clean_line = line.strip(" -•*|·°º\t,")

                # 3. Check for combined Degree + Institution in single line
                if not degree or not institution:
                    split_deg, split_inst = self._split_degree_institution(clean_line)
                    if split_deg and split_inst:
                        if not degree:
                            degree = split_deg
                        if not institution:
                            institution = split_inst
                        continue

                # 4. Standalone Degree
                if any(kw in lower_line for kw in DEGREE_KEYWORDS) and not degree:
                    degree = clean_line
                    continue

                # 5. Standalone Institution
                if any(kw in lower_line for kw in COLLEGE_KEYWORDS) and not institution:
                    institution = clean_line
                    continue

            # Fallback with spaCy NER if still missing
            if self.nlp:
                doc = self.nlp(block)
                for ent in doc.ents:
                    if ent.label_ == "DEGREE" and not degree:
                        degree = ent.text.strip()
                    elif ent.label_ == "ORG" and not institution:
                        ent_lower = ent.text.lower()
                        if any(kw in ent_lower for kw in COLLEGE_KEYWORDS) and not CURRICULUM_OR_DESC_REGEX.search(ent.text):
                            institution = ent.text.strip()

            # Clean up if degree was mistakenly set to a standalone date string
            if degree and (DATE_FULL_RANGE_REGEX.fullmatch(degree.strip()) or DATE_SINGLE_REGEX.fullmatch(degree.strip())):
                if not dates:
                    dates = degree
                degree = ""

            # Clean up if institution was mistakenly set to curriculum/course line
            if institution and (CURRICULUM_OR_DESC_REGEX.search(institution) or institution.startswith(("-", "•", "*"))):
                institution = ""

            # Deduplicate / filter any education entry where both institution and degree are empty
            if degree or institution:
                entries.append({
                    "institution": institution,
                    "degree": degree,
                    "dates": dates
                })

        return entries

    def extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract structured project records."""
        if not text.strip():
            return []

        entries: List[Dict[str, str]] = []
        blocks = self._split_into_entry_blocks(text)

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            name = lines[0].strip(" -•*|·°º\t")
            desc = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

            if name:
                entries.append({
                    "name": name,
                    "description": desc
                })

        return entries

    def _split_into_entry_blocks(self, text: str) -> List[str]:
        """Split section text into distinct entry chunks using multi-line spacing or entry markers."""
        raw_blocks = re.split(r"\n\s*\n+", text.strip())
        blocks = [b.strip() for b in raw_blocks if b.strip()]

        if len(blocks) <= 1 and "\n" in text:
            lines = text.split("\n")
            reconstructed_blocks: List[List[str]] = []
            current_block: List[str] = []

            for line in lines:
                clean_l = line.strip()
                if not clean_l:
                    continue

                # 1. Bullet lines and curriculum lines ALWAYS attach to current entry
                if clean_l.startswith(("-", "•", "*", "·", "°", "º", "—", "–", ">")) or CURRICULUM_OR_DESC_REGEX.search(clean_l):
                    current_block.append(line)
                    continue

                # 2. Date lines attach directly to current entry block
                if DATE_FULL_RANGE_REGEX.search(line) or DATE_SINGLE_REGEX.search(line):
                    current_block.append(line)
                    continue

                # 3. Check for new header only if line does NOT start with a bullet and is short
                is_header_split, _ = self._split_title_company(clean_l)
                is_standalone_header = (
                    any(kw in clean_l.lower() for kw in (JOB_TITLE_KEYWORDS + DEGREE_KEYWORDS))
                    and len(clean_l.split()) <= 7
                    and not any(punct in clean_l for punct in [".", ";"])
                )

                if (is_header_split or is_standalone_header) and len(current_block) >= 2:
                    # New distinct entry detected
                    reconstructed_blocks.append(current_block)
                    current_block = [line]
                else:
                    current_block.append(line)

            if current_block:
                reconstructed_blocks.append(current_block)

            if len(reconstructed_blocks) > 1:
                return ["\n".join(b).strip() for b in reconstructed_blocks]

        return blocks
