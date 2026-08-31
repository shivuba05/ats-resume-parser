# Resume Intelligence & ATS Studio ⚡

An enterprise-grade, deterministic, NLP-powered Applicant Tracking System (ATS) engine and recruiter analytics dashboard built with Python, spaCy, RapidFuzz, and Streamlit.

---

## 🌟 Key Highlights & Features

- **Autonomous Document Ingestion**: Native text extraction for both **PDF** (`pdfminer.six` / `pypdf`) and **Word DOCX** (`python-docx` + fallback ZIP-XML).
- **Precision Section Segmentation**: Taxonomy-driven section isolation preventing boundary leaks across Contact, Summary, Experience, Education, and Skills.
- **Robust Contact Extraction**: Heuristic and NLP person name detection, RFC 5322 email parsing, standardized international phone number formatting (`+1 (xxx) xxx-xxxx`), and portfolio/LinkedIn extraction (clean schema without address noise).
- **Reliable Experience & Education Parser**:
  - Delimiter and whitespace-separated title/company splitting (`Title at Company`, `Title - Company`, `Title | Company`, `Title    Company`).
  - Fail-closed company extraction ensuring description lines or dates are never consumed as company placeholders.
  - Bullet continuation preservation preventing sentence fragments from creating fake job entries.
  - Institution vs. Degree disambiguation ensuring curriculum lines (e.g. `Course Curriculum: ...`) are never assigned as school names.
- **Semantic Skill Graph & Ontology Matcher**:
  - 75+ canonical skills across Languages, Frontend, Backend, Databases, Cloud & DevOps, AI/Data Science, Security, and Methodologies.
  - Exact symbol-aware regex matching (`C++`, `C#`, `.NET`, `CI/CD`, `Node.js`).
  - RapidFuzz `token_sort_ratio` with token count and length alignment guards to eliminate false positives.
  - Built-in debug logging tracing source substrings and similarity scores.
- **High-End Dark SaaS Dashboard (`app.py`)**:
  - Polished dark theme with Electric Indigo (`#6366F1`) and Emerald accents.
  - Google Fonts pairing (*Plus Jakarta Sans* + *Inter* + *JetBrains Mono*).
  - Custom glowing metric cards, pill-shaped skill badges, and responsive candidate profile card.
  - Live Target Job Description Alignment & Missing Skill Gap Analysis.
  - Interactive Styled HTML Resume Template Previews (Modern Two-Column & Classic Executive).
  - Single-source-of-truth ATS JSON Inspector and one-click JSON download with real-time cache-busting.

---

## 📁 Repository Structure

```
shivu1/
├── parser/
│   ├── __init__.py           # Package initialization & exports
│   ├── extractor.py          # PDF & DOCX raw text extraction engine
│   ├── cleaner.py            # Unicode normalization, bullet standardizer, divider stripper
│   ├── segmenter.py          # Boundary-safe section splitter (Contact, Experience, Education, etc.)
│   ├── contact_extractor.py  # Name, email, standardized phone (+1/intl), LinkedIn, Portfolio
│   ├── ner_extractor.py      # spaCy pipeline + custom EntityRuler for degrees, orgs, and experience
│   ├── skill_matcher.py      # Exact regex + RapidFuzz matcher against skills ontology with debug mode
│   ├── template_renderer.py  # Modern Two-Column & Classic Executive HTML resume generators
│   └── resume_parser.py      # ResumeParser master orchestrator assembling standard ATS JSON
├── data/
│   └── skills_ontology.json  # Comprehensive taxonomy of 75+ canonical skills and alias mappings
├── tests/
│   ├── generate_samples.py   # Sample resume generator for testing
│   ├── sample_resumes/       # Benchmark DOCX and PDF test resumes
│   ├── test_parser.py        # Focused unit and integration test suite (11 test cases)
│   └── test_batch.py         # Batch verification runner across all sample resumes
├── app.py                    # Streamlit ATS Recruiter Dashboard web application
├── requirements.txt          # Python package dependencies
└── README.md                 # Project architecture & documentation
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10+
- `pip` package manager

### 2. Clone and Install Dependencies
```bash
git clone <repository_url>
cd shivu1
pip install -r requirements.txt
```

### 3. Download spaCy NLP Model
```bash
python -m spacy download en_core_web_sm
```

---

## 🚀 Running the Web Application

Launch the Streamlit ATS Intelligence Studio:
```bash
streamlit run app.py
```

Open your browser at **`http://localhost:8501`** (or the port displayed in your terminal).

### Dashboard Capabilities:
1. **Document Ingestion**: Upload any `.pdf` / `.docx` file, select from pre-built benchmark resumes, or paste raw text.
2. **Empty Initial State**: Clean waiting state by default — analytics render only when a resume is loaded.
3. **In-Page Engine Controls**: Adjust fuzzy matching sensitivity threshold (60–100) directly on the main page or in the sidebar.
4. **ATS Metric Cards**: Real-time completeness score, skills verified, milestones, credentials, and projects.
5. **Target Job Matcher**: Paste job descriptions to calculate alignment percentage and visual missing skill badges.
6. **Multi-Format Export**: One-click download for ATS JSON schema and styled HTML resume templates.

---

## 💻 Python API Usage

You can use the parser directly in your Python code or backend services:

```python
from parser.resume_parser import ResumeParser

# Initialize the parser engine
parser = ResumeParser(skill_fuzzy_threshold=85.0)

# 1. Parse from file path (PDF or DOCX)
result = parser.parse_file("tests/sample_resumes/1_senior_software_engineer.docx")

# 2. Or parse directly from raw text string
# result = parser.parse_text(raw_resume_text)

# Access structured data:
print("Candidate Name:", result["contact"]["name"])
print("Phone:", result["contact"]["phone"])
print("Skills Matched:", result["skills"])
print("Experience Milestones:", len(result["experience"]))
```

---

## 📋 Standard ATS JSON Schema Specification

```json
{
  "contact": {
    "name": "Alexander Hayes",
    "email": "alex.hayes@email.com",
    "phone": "+1 (415) 555-0192",
    "linkedin": "https://www.linkedin.com/in/alex-hayes",
    "portfolio": "https://github.com/alexhayes"
  },
  "summary": "Senior Backend & Distributed Systems Engineer with 8+ years building high-concurrency microservices and cloud infrastructure.",
  "experience": [
    {
      "company": "Stripe",
      "title": "Lead Software Engineer",
      "dates": "Jan 2021 - Present",
      "description": "- Designed and deployed mission-critical payment settlement services handling 50k requests/sec.\n- Migrated legacy monolithic architecture to Docker and Kubernetes on AWS.\n- Implemented high-throughput event processing pipelines using Apache Kafka and PostgreSQL."
    },
    {
      "company": "Uber",
      "title": "Senior Software Engineer",
      "dates": "Mar 2018 - Dec 2020",
      "description": "- Engineered real-time driver dispatching systems in Go and Python.\n- Optimized Redis caching layer, decreasing latency by 35%."
    }
  ],
  "education": [
    {
      "institution": "University of California, Berkeley",
      "degree": "Bachelor of Science in Computer Science",
      "dates": "2014 - 2018"
    }
  ],
  "skills": [
    "Amazon Web Services (AWS)",
    "Apache Kafka",
    "CI/CD",
    "Docker",
    "FastAPI",
    "Git",
    "Go",
    "Java",
    "Kubernetes",
    "Microservices",
    "PostgreSQL",
    "Python",
    "Redis",
    "Unit Testing"
  ],
  "projects": [
    {
      "name": "Distributed Task Queue",
      "description": "High-performance open-source task queue built in Go with Redis broker."
    }
  ],
  "certifications": [],
  "languages": [],
  "hobbies": []
}
```

---

## 🧠 Pipeline Architecture & Engine Details

### 1. Extraction & Cleaner (`extractor.py`, `cleaner.py`)
- Extracts paragraph blocks and table structures from DOCX, text streams from PDF.
- Normalizes unicode typography, non-standard bullets (`•`, `*`, `▪`, `⁃`, `·`, `°`, `º`) into `- `, collapses redundant blank lines, and removes page numbering artifacts.

### 2. Section Segmentation (`segmenter.py`)
- Classifies section boundaries using an extensive synonym index.
- Confines contact metadata strictly to the top header lines, eliminating section boundary leakage.

### 3. Contact & Phone Normalization (`contact_extractor.py`)
- Standardizes international and domestic phone numbers into `+1 (xxx) xxx-xxxx` / `+91 xxxxx xxxxx` formats while suppressing dates (`2018-2022`).
- Detects RFC 5322 emails, LinkedIn handles, and GitHub/personal portfolio links.
- Employs capitalized name heuristics combined with spaCy NER `PERSON` entities.

### 4. Semantic NER & Block Parser (`ner_extractor.py`)
- **Experience Parsing**: Splits header lines using standard punctuation and multiple whitespace tabs (`\s{2,}`). Fails closed to avoid capturing unrelated lines as company placeholders.
- **Continuation Bullets**: Bullet lines attach directly to active job descriptions without triggering fragmented fake entries.
- **Education Parser**: Disambiguates single-line `Degree, Institution` entries and attaches standalone date lines to the parent degree. Guards against assigning curriculum or coursework descriptions as institution names.

### 5. Skill Matcher & Taxonomy (`skill_matcher.py`, `data/skills_ontology.json`)
- Pre-indexes canonical names, category buckets, and aliases across 75+ tech domains.
- Executes symbol-safe exact regex and RapidFuzz `token_sort_ratio` matching with token count alignment to eliminate subtoken false positives.
- Supports `debug=True` mode for traceable skill extraction auditing.

---

## 🧪 Testing & Verification

Run the comprehensive unit test suite:
```bash
python -m unittest tests/test_parser.py
```

Run batch verification across all sample benchmark resumes:
```bash
python tests/test_batch.py
```

---

## 📄 License
This project is open source and available under the MIT License.
