"""
Pytest configuration and shared fixtures for resume_parser tests.
"""

import pytest
import tempfile
from pathlib import Path

from resume_parser.models.resume_data import ResumeData
from resume_parser.extractors.strategies import RegexExtractionStrategy
from resume_parser.extractors.name_extractor import NameExtractor
from resume_parser.extractors.email_extractor import EmailExtractor
from resume_parser.extractors.skills_extractor import SkillsExtractor
from resume_parser.core.resume_extractor import ResumeExtractor
from resume_parser.core.framework import ResumeParserFramework


@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing."""
    return """
John Michael Smith
Email: john.smith@example.com
Phone: +1 (555) 123-4567

PROFESSIONAL SUMMARY
Experienced software engineer with expertise in Python, AWS, and Docker.

TECHNICAL SKILLS
Languages: Python, Java, C++, JavaScript
Cloud Platforms: AWS, Azure, Google Cloud
Tools & Frameworks: Django, Flask, FastAPI, React, Kubernetes

EXPERIENCE
Senior Software Engineer at TechCorp (2020-Present)
- Led development of microservices using Docker and Kubernetes
- Managed cloud infrastructure on AWS and Azure
- Mentored junior developers in Python best practices

EDUCATION
B.S. Computer Science, State University (2016)
"""


@pytest.fixture
def sample_resume_data():
    """Expected ResumeData for sample resume."""
    return ResumeData(
        name="John Michael Smith",
        email="john.smith@example.com",
        skills=["Python", "AWS", "Docker", "Java", "C++", "JavaScript",
                "Django", "Flask", "FastAPI", "React", "Kubernetes"]
    )


@pytest.fixture
def regex_strategy():
    """Regex extraction strategy instance."""
    return RegexExtractionStrategy()


@pytest.fixture
def basic_extractors():
    """Basic set of field extractors with regex strategy."""
    return {
        "name": NameExtractor(),
        "email": EmailExtractor(),
        "skills": SkillsExtractor(),
    }


@pytest.fixture
def resume_extractor(basic_extractors):
    """ResumeExtractor instance with basic extractors."""
    return ResumeExtractor(basic_extractors)


@pytest.fixture
def resume_parser_framework(resume_extractor):
    """ResumeParserFramework instance."""
    return ResumeParserFramework(resume_extractor)


@pytest.fixture
def temp_pdf_file():
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_docx_file():
    """Create a temporary DOCX file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def temp_text_file():
    """Create a temporary text file with content."""
    content = "This is a test resume text file."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        if "slow" in str(item.name).lower():
            item.add_marker(pytest.mark.slow)