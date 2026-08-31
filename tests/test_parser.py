"""Focused test suite for Resume Parser ATS Engine.

Targeting contact_extractor, skill_matcher, ner_extractor, and basic pipeline assembly.
"""

from pathlib import Path
import tempfile
import unittest

from parser.contact_extractor import (
    extract_contact_info,
    extract_email,
    extract_github_or_portfolio,
    extract_linkedin,
    extract_name_heuristic,
    extract_phone,
    format_phone,
)
from parser.extractor import UnsupportedFormatError
from parser.resume_parser import ResumeParser
from parser.skill_matcher import SkillMatcher


class TestContactExtractor(unittest.TestCase):
    """Unit tests for contact info regex, heuristics, and phone formatting."""

    def test_extract_email(self):
        text = "Please reach out to dev_john.doe@company.co.uk or jane@test.com"
        email = extract_email(text)
        self.assertEqual(email, "dev_john.doe@company.co.uk")

    def test_extract_phone_formats(self):
        self.assertEqual(extract_phone("Contact: +1 (555) 234-5678"), "+1 (555) 234-5678")
        self.assertEqual(extract_phone("Phone: +91 98765 43210"), "+91 98765 43210")
        self.assertEqual(extract_phone("Mobile: 3868683442"), "+1 (386) 868-3442")

    def test_format_phone(self):
        self.assertEqual(format_phone("3868683442"), "+1 (386) 868-3442")
        self.assertEqual(format_phone("14155550192"), "+1 (415) 555-0192")

    def test_extract_linkedin_and_portfolio(self):
        text = "LinkedIn: https://www.linkedin.com/in/sarah-connor GitHub: https://github.com/sarahc"
        linkedin = extract_linkedin(text)
        portfolio = extract_github_or_portfolio(text, linkedin_url=linkedin)
        self.assertEqual(linkedin, "https://www.linkedin.com/in/sarah-connor")
        self.assertEqual(portfolio, "https://github.com/sarahc")

    def test_extract_name_heuristic(self):
        header = "Sarah Connor\nsarah@sky.net | +1 555-0100\nSenior AI Engineer"
        name = extract_name_heuristic(header)
        self.assertEqual(name, "Sarah Connor")

    def test_extract_contact_info_full(self):
        text = (
            "Michael Scott\n"
            "mscott@dundermifflin.com | +1 570-555-0123\n"
            "https://www.linkedin.com/in/michael-scott\n"
            "https://github.com/greatscott\n"
        )
        contact = extract_contact_info(text)
        self.assertEqual(contact["name"], "Michael Scott")
        self.assertEqual(contact["email"], "mscott@dundermifflin.com")
        self.assertIsNotNone(contact["phone"])
        self.assertEqual(contact["linkedin"], "https://www.linkedin.com/in/michael-scott")
        self.assertEqual(contact["portfolio"], "https://github.com/greatscott")
        self.assertNotIn("address", contact)


class TestSkillMatcher(unittest.TestCase):
    """Unit tests for ontology-based exact and fuzzy skill matching."""

    def test_skill_matcher_exact_and_fuzzy(self):
        matcher = SkillMatcher()
        sample_text = (
            "Strong experience in React.js, Python3, Docker, and ML algorithms. "
            "Proficient with Postgres databases, C++, K8s, and PyTest."
        )
        skills = matcher.extract_skills(sample_text)

        self.assertIn("React", skills)
        self.assertIn("Python", skills)
        self.assertIn("Docker", skills)
        self.assertIn("Machine Learning", skills)
        self.assertIn("PostgreSQL", skills)
        self.assertIn("C++", skills)
        self.assertIn("Kubernetes", skills)
        self.assertIn("Unit Testing", skills)

    def test_no_false_positive_skill_matches(self):
        matcher = SkillMatcher()
        # "SKILLS" section header or generic word should not trigger "Investigation Skills"
        sample_text = "SKILLS\nPython, Docker, AWS"
        skills = matcher.extract_skills(sample_text)
        self.assertNotIn("Investigation Skills", skills)
        self.assertNotIn("Cassandra", skills)
        self.assertNotIn("Computer Vision", skills)


class TestResumeParserBasic(unittest.TestCase):
    """Integration check for pipeline execution against benchmark resumes."""

    def setUp(self):
        self.parser = ResumeParser()

    def test_parse_senior_software_engineer(self):
        sample_docx = Path("tests/sample_resumes/1_senior_software_engineer.docx")
        if sample_docx.exists():
            data = self.parser.parse_file(str(sample_docx))
            # 1. Contact assertions (no address field, formatted phone)
            self.assertEqual(data["contact"]["name"], "Alexander Hayes")
            self.assertEqual(data["contact"]["email"], "alex.hayes@email.com")
            self.assertEqual(data["contact"]["phone"], "+1 (415) 555-0192")
            self.assertEqual(data["contact"]["linkedin"], "https://www.linkedin.com/in/alex-hayes")
            self.assertEqual(data["contact"]["portfolio"], "https://github.com/alexhayes")
            self.assertNotIn("address", data["contact"])

            # 2. Experience assertions: company = Stripe and Uber (no fake entries)
            self.assertEqual(len(data["experience"]), 2)
            self.assertEqual(data["experience"][0]["company"], "Stripe")
            self.assertEqual(data["experience"][0]["title"], "Lead Software Engineer")
            self.assertEqual(data["experience"][1]["company"], "Uber")
            self.assertEqual(data["experience"][1]["title"], "Senior Software Engineer")

            # 3. Education assertions: 1 clean entry with correct dates
            self.assertEqual(len(data["education"]), 1)
            self.assertEqual(data["education"][0]["degree"], "Bachelor of Science in Computer Science")
            self.assertEqual(data["education"][0]["institution"], "University of California, Berkeley")
            self.assertEqual(data["education"][0]["dates"], "2014 - 2018")

            # 4. Skill assertions: no Investigation Skills
            self.assertIn("Python", data["skills"])
            self.assertIn("Docker", data["skills"])
            self.assertNotIn("Investigation Skills", data["skills"])
            self.assertNotIn("Cassandra", data["skills"])
            self.assertNotIn("Computer Vision", data["skills"])

    def test_parse_robert_cooper_creative(self):
        sample_docx = Path("tests/sample_resumes/robert_cooper_security_guard.docx")
        if sample_docx.exists():
            data = self.parser.parse_file(str(sample_docx))
            # 1. Contact assertions (no address field, formatted phone)
            self.assertEqual(data["contact"]["name"], "Robert Cooper")
            self.assertEqual(data["contact"]["email"], "email@email.com")
            self.assertEqual(data["contact"]["phone"], "+1 (386) 868-3442")
            self.assertNotIn("address", data["contact"])

            # 2. Experience assertions: exactly 2 entries (ADT Security, Copwatch) - no fake entries from continuation bullets
            self.assertEqual(len(data["experience"]), 2)
            self.assertIn("ADT Security", data["experience"][0]["company"])
            self.assertIn("Copwatch", data["experience"][1]["company"])

            # 3. Education assertions: 3 entries with real institutions, NO "Course Curriculum" as institution
            self.assertEqual(len(data["education"]), 3)
            for edu in data["education"]:
                self.assertNotIn("Course Curriculum", edu["institution"])
                self.assertNotIn("Course Curriculum", edu["degree"])

            # 4. Skill assertions: Genuine Investigation Skills & Physical Combat & Martial Arts
            self.assertIn("Investigation Skills", data["skills"])
            self.assertIn("Physical Combat & Martial Arts", data["skills"])
            self.assertIn("Criminal Justice", data["skills"])

    def test_extractor_unsupported_format(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"plain text")
            tmp_path = tmp.name

        try:
            with self.assertRaises(UnsupportedFormatError):
                self.parser.parse_file(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
