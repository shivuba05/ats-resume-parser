"""Batch verification script to parse all sample resumes in tests/sample_resumes/."""

import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from parser.resume_parser import ResumeParser


def test_batch_sample_resumes():
    parser = ResumeParser()
    sample_dir = Path(__file__).resolve().parent / "sample_resumes"
    sample_files = sorted(list(sample_dir.glob("*.*")))

    print(f"Testing batch parsing on {len(sample_files)} sample resumes...\n")
    success_count = 0

    for file_path in sample_files:
        if file_path.suffix.lower() not in [".pdf", ".docx"]:
            continue

        try:
            result = parser.parse_file(str(file_path))
            # Verify top-level keys
            required_keys = ["contact", "summary", "experience", "education", "skills", "projects"]
            for k in required_keys:
                assert k in result, f"Missing key '{k}' in result for {file_path.name}"

            # Verify contact keys (no address in standard schema)
            for ck in ["name", "email", "phone", "linkedin", "portfolio"]:
                assert ck in result["contact"], f"Missing contact key '{ck}' for {file_path.name}"
            assert "address" not in result["contact"], f"Unexpected 'address' key found for {file_path.name}"

            name = result['contact']['name'] or 'N/A'
            print(f"[PASS] [{file_path.suffix.upper()[1:]}] {file_path.name:<35} | Name: {name:<20} | Skills: {len(result['skills']):<3} | Exp: {len(result['experience']):<2} | Edu: {len(result['education'])}")
            success_count += 1
        except Exception as e:
            print(f"[FAIL] {file_path.name}: {e}")
            raise

    print(f"\nSuccessfully parsed {success_count}/{len(sample_files)} sample resumes!")


if __name__ == "__main__":
    test_batch_sample_resumes()
