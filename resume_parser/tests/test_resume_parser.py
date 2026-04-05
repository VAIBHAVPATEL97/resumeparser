"""
Comprehensive unit tests for the Resume Parser framework.

Tests cover all components with happy paths and edge cases:
- Models (ResumeData)
- Extractors (strategies and field extractors)
- Parsers (file format parsers)
- Core (framework, extractor orchestration)
- Utils (logging)

Run with: python -m pytest tests/ -v
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

# Import all components to test
from resume_parser.models.resume_data import ResumeData
from resume_parser.extractors.strategies import (
    RegexExtractionStrategy,
    NERExtractionStrategy,
    LLMExtractionStrategy,
)
from resume_parser.extractors.base import FieldExtractor
from resume_parser.extractors.name_extractor import NameExtractor
from resume_parser.extractors.email_extractor import EmailExtractor
from resume_parser.extractors.skills_extractor import SkillsExtractor
from resume_parser.core.resume_extractor import ResumeExtractor, ResumeParsingError
from resume_parser.core.framework import ResumeParserFramework
from resume_parser.parsers.base import BaseParser, FileParserError
from resume_parser.parsers.pdf_parser import PDFParser
from resume_parser.parsers.word_parser import WordParser
from resume_parser.core.parser_factory import get_parser
from resume_parser.utils.logger import configure_logging


# Test data constants
SAMPLE_RESUME_TEXT = """
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

SAMPLE_RESUME_DATA = {
    "name": "John Michael Smith",
    "email": "john.smith@example.com",
    "skills": ["Python", "AWS", "Docker", "Java", "C++", "JavaScript", "Django", "Flask", "FastAPI", "React", "Kubernetes"]
}


@pytest.mark.unit
class TestResumeData:
    """Test ResumeData dataclass functionality."""

    def test_resume_data_creation(self):
        """Test basic ResumeData creation and defaults."""
        data = ResumeData()
        assert data.name == ""
        assert data.email == ""
        assert data.skills == []

    def test_resume_data_with_values(self):
        """Test ResumeData with provided values."""
        data = ResumeData(
            name="John Doe",
            email="john@example.com",
            skills=["Python", "AWS"]
        )
        assert data.name == "John Doe"
        assert data.email == "john@example.com"
        assert data.skills == ["Python", "AWS"]

    def test_resume_data_as_dict(self):
        """Test as_dict() method returns correct JSON-serializable dict."""
        data = ResumeData(
            name="John Doe",
            email="john@example.com",
            skills=["Python", "AWS"]
        )
        expected = {
            "name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python", "AWS"]
        }
        assert data.as_dict() == expected

    def test_resume_data_repr(self):
        """Test string representation."""
        data = ResumeData(name="John Doe", email="john@example.com")
        repr_str = repr(data)
        assert "John Doe" in repr_str
        assert "john@example.com" in repr_str

    def test_resume_data_empty_skills_list(self):
        """Test that skills defaults to empty list, not None."""
        data = ResumeData()
        assert isinstance(data.skills, list)
        assert len(data.skills) == 0

    def test_resume_data_skills_immutable_copy(self):
        """Test that as_dict() returns a copy of skills list."""
        original_skills = ["Python", "AWS"]
        data = ResumeData(skills=original_skills)
        dict_result = data.as_dict()

        # Modify original list
        original_skills.append("Docker")

        # Dict should still have original skills
        assert dict_result["skills"] == ["Python", "AWS"]


@pytest.mark.unit
class TestRegexExtractionStrategy:
    """Test RegexExtractionStrategy functionality."""

    def setup_method(self):
        """Set up test instance."""
        self.strategy = RegexExtractionStrategy()

    def test_extract_name_happy_path(self):
        """Test name extraction with well-formatted resume."""
        name = self.strategy.extract_name(SAMPLE_RESUME_TEXT)
        assert name == "John Michael Smith"

    def test_extract_name_edge_cases(self):
        """Test name extraction edge cases."""
        # Empty text
        assert self.strategy.extract_name("") is None
        assert self.strategy.extract_name(None) is None

        # No name-like content
        no_name_text = "This is just some random text without any names."
        assert self.strategy.extract_name(no_name_text) is None

        # Name at end of file
        late_name_text = """
        Some content here
        More content
        John Doe
        """
        assert self.strategy.extract_name(late_name_text) == "John Doe"

    def test_extract_email_happy_path(self):
        """Test email extraction with valid email."""
        email = self.strategy.extract_email(SAMPLE_RESUME_TEXT)
        assert email == "john.smith@example.com"

    def test_extract_email_edge_cases(self):
        """Test email extraction edge cases."""
        # Empty text
        assert self.strategy.extract_email("") is None

        # No email
        no_email_text = "This text has no email address."
        assert self.strategy.extract_email(no_email_text) is None

        # Multiple emails (returns first)
        multi_email_text = "Contact: first@example.com or second@example.com"
        assert self.strategy.extract_email(multi_email_text) == "first@example.com"

        # Invalid email formats
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user.example.com"
        ]
        for invalid in invalid_emails:
            text = f"Contact: {invalid}"
            result = self.strategy.extract_email(text)
            assert result is None or "@" not in result or "." not in result

    def test_extract_skills_happy_path(self):
        """Test skills extraction with known keywords."""
        skills = self.strategy.extract_skills(SAMPLE_RESUME_TEXT)
        expected_skills = {"python", "java", "c++", "javascript", "aws", "azure", "django", "flask", "fastapi", "react", "kubernetes", "docker"}
        extracted_skills = set(skill.lower() for skill in skills)
        assert expected_skills.issubset(extracted_skills)

    def test_extract_skills_edge_cases(self):
        """Test skills extraction edge cases."""
        # Empty text
        assert self.strategy.extract_skills("") == []

        # No skills
        no_skills_text = "This resume has no technical skills mentioned."
        assert self.strategy.extract_skills(no_skills_text) == []

        # Skills with different cases
        mixed_case_text = "Skills: PYTHON, aws, Docker"
        skills = self.strategy.extract_skills(mixed_case_text)
        assert "python" in [s.lower() for s in skills]
        assert "aws" in [s.lower() for s in skills]
        assert "docker" in [s.lower() for s in skills]

        # Skills with special characters
        special_text = "Skills: C++, C#, Node.js"
        skills = self.strategy.extract_skills(special_text)
        assert "c++" in [s.lower() for s in skills]
        assert "c#" in [s.lower() for s in skills]
        assert "node.js" in [s.lower() for s in skills]


@pytest.mark.unit
class TestNERExtractionStrategy:
    """Test NERExtractionStrategy (placeholder implementation)."""

    def setup_method(self):
        """Set up test instance."""
        self.strategy = NERExtractionStrategy()

    def test_extract_name_placeholder(self):
        """Test that NER extraction returns None (placeholder)."""
        result = self.strategy.extract_name(SAMPLE_RESUME_TEXT)
        assert result is None

    def test_extract_email_placeholder(self):
        """Test that NER extraction returns None (placeholder)."""
        result = self.strategy.extract_email(SAMPLE_RESUME_TEXT)
        assert result is None

    def test_extract_skills_placeholder(self):
        """Test that NER extraction returns empty list (placeholder)."""
        result = self.strategy.extract_skills(SAMPLE_RESUME_TEXT)
        assert result == []


@pytest.mark.unit
class TestLLMExtractionStrategy:
    """Test LLMExtractionStrategy functionality."""

    def setup_method(self):
        """Set up test instance without requiring the google-genai package."""
        self.strategy = None

    @patch('google.genai.Client', create=True)
    def test_extract_name_with_mock_gemini(self, mock_client_class):
        """Test name extraction with mocked Gemini API."""
        # Mock the Gemini client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"name": "Jane Doe", "email": null, "skills": []}'
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create strategy with mocked client
        strategy = LLMExtractionStrategy(api_key="test-key")
        strategy._client = mock_client

        result = strategy.extract_name("test resume")
        assert result == "Jane Doe"

    @patch('google.genai.Client', create=True)
    def test_extract_email_with_mock_gemini(self, mock_client_class):
        """Test email extraction with mocked Gemini API."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"name": null, "email": "jane@example.com", "skills": []}'
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        strategy = LLMExtractionStrategy(api_key="test-key")
        strategy._client = mock_client

        result = strategy.extract_email("test resume")
        assert result == "jane@example.com"

    @patch('google.genai.Client', create=True)
    def test_extract_skills_with_mock_gemini(self, mock_client_class):
        """Test skills extraction with mocked Gemini API."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"name": null, "email": null, "skills": ["Python", "AWS"]}'
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        strategy = LLMExtractionStrategy(api_key="test-key")
        strategy._client = mock_client

        result = strategy.extract_skills("test resume")
        assert set(result) == {"Python", "AWS"}

    @patch('google.genai.Client', create=True)
    def test_llm_strategy_without_api_key(self, mock_client_class):
        """Test LLM strategy initialization without API key."""
        mock_client_class.return_value = None  # Simulate no client created
        
        strategy = LLMExtractionStrategy()
        # The client should be None when no API key is provided
        assert strategy._client is None

        # Should return None for all extractions
        assert strategy.extract_name("test") is None
        assert strategy.extract_email("test") is None
        assert strategy.extract_skills("test") == []

    @patch('google.genai.Client', create=True)
    def test_llm_caching(self, mock_client_class):
        """Test that LLM results are cached to avoid repeated API calls."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"name": "Cached Name", "email": null, "skills": []}'
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        strategy = LLMExtractionStrategy(api_key="test-key")
        strategy._client = mock_client

        # First call should make API request
        result1 = strategy.extract_name("test resume")
        assert result1 == "Cached Name"
        assert mock_client.models.generate_content.call_count == 1

        # Second call with same text should use cache
        result2 = strategy.extract_name("test resume")
        assert result2 == "Cached Name"
        assert mock_client.models.generate_content.call_count == 1  # Still 1 call

    @patch('google.genai.Client', create=True)
    def test_llm_invalid_json_response(self, mock_client_class):
        """Test handling of invalid JSON response from Gemini."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = "Invalid JSON response"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client

        strategy = LLMExtractionStrategy(api_key="test-key")
        strategy._client = mock_client

        result = strategy.extract_name("test resume")
        assert result is None


@pytest.mark.unit
class TestFieldExtractors:
    """Test field extractor wrapper classes."""

    def test_name_extractor_with_regex_strategy(self):
        """Test NameExtractor with default strategy."""
        extractor = NameExtractor()
        assert isinstance(extractor.strategy, (LLMExtractionStrategy, RegexExtractionStrategy))

        # Test with explicit regex strategy
        regex_extractor = NameExtractor(strategy=RegexExtractionStrategy())
        assert isinstance(regex_extractor.strategy, RegexExtractionStrategy)

        result = regex_extractor.extract(SAMPLE_RESUME_TEXT)
        assert result == "John Michael Smith"

    def test_email_extractor_with_regex_strategy(self):
        """Test EmailExtractor with default strategy."""
        extractor = EmailExtractor()
        assert isinstance(extractor.strategy, (LLMExtractionStrategy, RegexExtractionStrategy))

        # Test with explicit regex strategy
        regex_extractor = EmailExtractor(strategy=RegexExtractionStrategy())
        assert isinstance(regex_extractor.strategy, RegexExtractionStrategy)

        result = regex_extractor.extract(SAMPLE_RESUME_TEXT)
        assert result == "john.smith@example.com"

    def test_skills_extractor_with_regex_strategy(self):
        """Test SkillsExtractor with default strategy."""
        extractor = SkillsExtractor()
        assert isinstance(extractor.strategy, (LLMExtractionStrategy, RegexExtractionStrategy))

        # Test with explicit regex strategy
        regex_extractor = SkillsExtractor(strategy=RegexExtractionStrategy())
        assert isinstance(regex_extractor.strategy, RegexExtractionStrategy)

        result = regex_extractor.extract(SAMPLE_RESUME_TEXT)
        assert isinstance(result, list)
        assert len(result) > 0
        assert "python" in [skill.lower() for skill in result]

    def test_extractors_with_custom_strategy(self):
        """Test extractors with custom strategy injection."""
        custom_strategy = RegexExtractionStrategy()
        extractor = NameExtractor(strategy=custom_strategy)
        assert extractor.strategy is custom_strategy

    def test_llm_failure_falls_back_to_regex(self):
        """Test that LLM failure triggers fallback to RegexExtractionStrategy."""

        class FailingLLMStrategy(LLMExtractionStrategy):
            def __init__(self):
                pass

            def extract_name(self, text: str):
                raise RuntimeError("429 RESOURCE_EXHAUSTED")

            def extract_email(self, text: str):
                raise RuntimeError("429 RESOURCE_EXHAUSTED")

            def extract_skills(self, text: str):
                raise RuntimeError("429 RESOURCE_EXHAUSTED")

        extractor = NameExtractor(strategy=FailingLLMStrategy())
        result = extractor.extract(SAMPLE_RESUME_TEXT)

        assert isinstance(extractor.strategy, RegexExtractionStrategy)
        assert result == "John Michael Smith"

    def test_extractors_with_empty_text(self):
        """Test extractors handle empty text gracefully."""
        extractor = NameExtractor()
        result = extractor.extract("")
        assert result is None

        extractor = EmailExtractor()
        result = extractor.extract("")
        assert result is None

        extractor = SkillsExtractor()
        result = extractor.extract("")
        assert result == []


@pytest.mark.unit
class TestResumeExtractor:
    """Test ResumeExtractor orchestration functionality."""

    def setup_method(self):
        """Set up test extractors."""
        self.extractors = {
            "name": NameExtractor(),
            "email": EmailExtractor(),
            "skills": SkillsExtractor(),
        }
        self.resume_extractor = ResumeExtractor(self.extractors)

    def test_resume_extractor_creation(self):
        """Test ResumeExtractor initialization."""
        assert self.resume_extractor.extractors == self.extractors

    def test_resume_extractor_extract_empty_text(self):
        """Test extraction with empty text."""
        result = self.resume_extractor.extract("")

        assert isinstance(result, ResumeData)
        assert result.name == ""
        assert result.email == ""
        assert result.skills == []

    def test_resume_extractor_extract_partial_data(self):
        """Test extraction with partial resume data."""
        partial_resume = "John Doe\nEmail: john@example.com"
        result = self.resume_extractor.extract(partial_resume)

        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        assert result.skills == []

    def test_resume_extractor_with_failing_extractor(self):
        """Test handling of extractor failures."""
        # Create a mock extractor that raises an exception
        failing_extractor = Mock()
        failing_extractor.extract.side_effect = Exception("Extraction failed")

        extractors_with_failure = {
            "name": failing_extractor,
            "email": EmailExtractor(),
        }
        extractor = ResumeExtractor(extractors_with_failure)

        with pytest.raises(ResumeParsingError, match="Field extraction for 'name' failed"):
            extractor.extract(SAMPLE_RESUME_TEXT)

    def test_resume_extractor_with_non_string_input(self):
        """Test that non-string input raises error."""
        with pytest.raises(ResumeParsingError, match="Extracted resume content must be a string"):
            self.resume_extractor.extract(123)


@pytest.mark.unit
class TestParsers:
    """Test file parser functionality."""

    def test_base_parser_validation_success(self):
        """Test BaseParser file validation with valid file."""
        # Create a concrete implementation for testing
        class TestParser(BaseParser):
            def load_text(self, file_path: str) -> str:
                return "test content"

        parser = TestParser()

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            path = parser._validate_file(temp_path)
            assert path.exists()
            assert path.is_file()
        finally:
            os.unlink(temp_path)

    def test_base_parser_validation_file_not_found(self):
        """Test BaseParser validation with non-existent file."""
        class TestParser(BaseParser):
            def load_text(self, file_path: str) -> str:
                return "test content"

        parser = TestParser()

        with pytest.raises(FileParserError, match="File not found"):
            parser._validate_file("/non/existent/file.txt")

    def test_base_parser_validation_directory(self):
        """Test BaseParser validation with directory instead of file."""
        class TestParser(BaseParser):
            def load_text(self, file_path: str) -> str:
                return "test content"

        parser = TestParser()

        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(FileParserError, match="Path is not a file"):
                parser._validate_file(temp_dir)

    @patch('resume_parser.parsers.pdf_parser.PdfReader')
    def test_pdf_parser_happy_path(self, mock_pdf_reader):
        """Test PDF parser with mocked PdfReader."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Page 1 content"
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name

        try:
            result = parser.load_text(temp_path)
            assert result == "Page 1 content"
        finally:
            os.unlink(temp_path)

    @patch('resume_parser.parsers.pdf_parser.PdfReader')
    def test_pdf_parser_empty_pdf(self, mock_pdf_reader):
        """Test PDF parser with empty PDF."""
        mock_reader = Mock()
        mock_reader.pages = []
        mock_pdf_reader.return_value = mock_reader

        parser = PDFParser()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name

        try:
            result = parser.load_text(temp_path)
            assert result == ""
        finally:
            os.unlink(temp_path)

    @patch('resume_parser.parsers.pdf_parser.PdfReader')
    def test_pdf_parser_pdf_read_error(self, mock_pdf_reader):
        """Test PDF parser error handling."""
        mock_pdf_reader.side_effect = Exception("PDF read error")

        parser = PDFParser()

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(FileParserError, match="Could not parse PDF"):
                parser.load_text(temp_path)
        finally:
            os.unlink(temp_path)

    @patch('resume_parser.parsers.word_parser.docx')
    def test_word_parser_happy_path(self, mock_docx):
        """Test Word parser with mocked docx."""
        mock_paragraph = Mock()
        mock_paragraph.text = "Paragraph 1"
        mock_document = Mock()
        mock_document.paragraphs = [mock_paragraph]
        mock_docx.Document.return_value = mock_document

        parser = WordParser()

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name

        try:
            result = parser.load_text(temp_path)
            assert result == "Paragraph 1"
        finally:
            os.unlink(temp_path)

    @patch('resume_parser.parsers.word_parser.docx')
    def test_word_parser_empty_document(self, mock_docx):
        """Test Word parser with empty document."""
        mock_document = Mock()
        mock_document.paragraphs = []
        mock_docx.Document.return_value = mock_document

        parser = WordParser()

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name

        try:
            result = parser.load_text(temp_path)
            assert result == ""
        finally:
            os.unlink(temp_path)

    @patch('resume_parser.parsers.word_parser.docx')
    def test_word_parser_docx_error(self, mock_docx):
        """Test Word parser error handling."""
        mock_docx.Document.side_effect = Exception("DOCX read error")

        parser = WordParser()

        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(FileParserError, match="Could not parse Word document"):
                parser.load_text(temp_path)
        finally:
            os.unlink(temp_path)


@pytest.mark.unit
class TestParserFactory:
    """Test parser factory functionality."""

    def test_get_parser_pdf(self):
        """Test parser factory returns PDFParser for .pdf files."""
        parser = get_parser("test.pdf")
        assert isinstance(parser, PDFParser)

    def test_get_parser_docx(self):
        """Test parser factory returns WordParser for .docx files."""
        parser = get_parser("test.docx")
        assert isinstance(parser, WordParser)

    def test_get_parser_doc(self):
        """Test parser factory returns WordParser for .doc files."""
        parser = get_parser("test.doc")
        assert isinstance(parser, WordParser)

    def test_get_parser_unsupported_extension(self):
        """Test parser factory raises error for unsupported extensions."""
        with pytest.raises(FileParserError, match="Unsupported file type"):
            get_parser("test.unsupported")

    def test_get_parser_case_insensitive(self):
        """Test parser factory is case insensitive."""
        parser = get_parser("test.PDF")
        assert isinstance(parser, PDFParser)

        parser = get_parser("test.DOCX")
        assert isinstance(parser, WordParser)


@pytest.mark.unit
class TestResumeParserFramework:
    """Test ResumeParserFramework orchestration."""

    def setup_method(self):
        """Set up test framework."""
        self.extractors = {
            "name": NameExtractor(strategy=RegexExtractionStrategy()),
            "email": EmailExtractor(strategy=RegexExtractionStrategy()),
            "skills": SkillsExtractor(strategy=RegexExtractionStrategy()),
        }
        self.resume_extractor = ResumeExtractor(self.extractors)
        self.framework = ResumeParserFramework(self.resume_extractor)

    @patch('resume_parser.core.framework.get_parser')
    def test_parse_resume_happy_path(self, mock_get_parser):
        """Test successful resume parsing."""
        # Mock parser
        mock_parser = Mock()
        mock_parser.load_text.return_value = SAMPLE_RESUME_TEXT
        mock_get_parser.return_value = mock_parser

        result = self.framework.parse_resume("test.pdf")

        assert isinstance(result, ResumeData)
        assert result.name == "John Michael Smith"
        assert result.email == "john.smith@example.com"
        assert len(result.skills) > 0

    @patch('resume_parser.core.framework.get_parser')
    def test_parse_resume_extractor_error(self, mock_get_parser):
        """Test framework handles extractor errors."""
        # Mock parser
        mock_parser = Mock()
        mock_parser.load_text.return_value = "test text"
        mock_get_parser.return_value = mock_parser

        # Create extractor that will fail
        failing_extractor = Mock()
        failing_extractor.extract.side_effect = Exception("Extraction failed")

        failing_extractors = {"name": failing_extractor}
        failing_resume_extractor = ResumeExtractor(failing_extractors)
        failing_framework = ResumeParserFramework(failing_resume_extractor)

        with pytest.raises(ResumeParsingError):
            failing_framework.parse_resume("test.pdf")

    def test_parse_resume_invalid_file_path(self):
        """Test framework handles invalid file paths."""
        with pytest.raises(ResumeParsingError):
            self.framework.parse_resume("")

        with pytest.raises(ResumeParsingError):
            self.framework.parse_resume(None)


@pytest.mark.unit
class TestLogger:
    """Test logging configuration."""

    def test_configure_logging(self):
        """Test that logging can be configured without errors."""
        # Should not raise any exceptions
        configure_logging()

        # Verify logger can be obtained
        import logging
        logger = logging.getLogger("test_logger")
        assert logger is not None


# Integration Tests
@pytest.mark.integration
class TestIntegration:
    """Integration tests combining multiple components."""

    @patch('resume_parser.core.framework.get_parser')
    def test_full_pipeline_pdf_parsing(self, mock_get_parser):
        """Test complete pipeline from PDF file to ResumeData."""
        # Mock parser
        mock_parser = Mock()
        mock_parser.load_text.return_value = SAMPLE_RESUME_TEXT
        mock_get_parser.return_value = mock_parser

        framework = ResumeParserFramework(ResumeExtractor({
            "name": NameExtractor(strategy=RegexExtractionStrategy()),
            "email": EmailExtractor(strategy=RegexExtractionStrategy()),
            "skills": SkillsExtractor(strategy=RegexExtractionStrategy()),
        }))

        result = framework.parse_resume("dummy.pdf")

        assert isinstance(result, ResumeData)
        assert result.name == "John Michael Smith"
        assert result.email == "john.smith@example.com"
        assert len(result.skills) > 0

    def test_strategy_switching(self):
        """Test switching between different extraction strategies."""
        # Test with regex strategy
        regex_extractor = NameExtractor(strategy=RegexExtractionStrategy())
        result_regex = regex_extractor.extract(SAMPLE_RESUME_TEXT)

        # Test with NER strategy (placeholder)
        ner_extractor = NameExtractor(strategy=NERExtractionStrategy())
        result_ner = ner_extractor.extract(SAMPLE_RESUME_TEXT)

        # Results should be different (regex finds name, NER returns None)
        assert result_regex is not None
        assert result_ner is None

    def test_multiple_extractors_same_strategy(self):
        """Test multiple extractors using the same strategy instance."""
        strategy = RegexExtractionStrategy()

        name_extractor = NameExtractor(strategy=strategy)
        email_extractor = EmailExtractor(strategy=strategy)
        skills_extractor = SkillsExtractor(strategy=strategy)

        result = ResumeExtractor({
            "name": name_extractor,
            "email": email_extractor,
            "skills": skills_extractor,
        }).extract(SAMPLE_RESUME_TEXT)

        assert result.name == "John Michael Smith"
        assert result.email == "john.smith@example.com"
        assert len(result.skills) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
