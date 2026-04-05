"""
Usage examples for different extraction strategies.

This demonstrates how to use the pluggable extraction strategies:
- RegexExtractionStrategy (default, fast, rule-based)
- NERExtractionStrategy (Named Entity Recognition, requires spacy/transformers) - Placeholder for future implementation
- LLMExtractionStrategy (Large Language Model, requires API keys or local LLM)
"""

import sys
from pathlib import Path

if __package__ is None:
    repo_root = Path(__file__).resolve().parents[1]  # Parent of resume_parser (resumeparser/)
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from resume_parser.extractors import (
    EmailExtractor,
    NameExtractor,
    SkillsExtractor,
)
from resume_parser.extractors.strategies import (
    RegexExtractionStrategy,
    NERExtractionStrategy,
    LLMExtractionStrategy,
)
from resume_parser.core.resume_extractor import ResumeExtractor
from resume_parser.core.framework import ResumeParserFramework
from resume_parser.utils.logger import configure_logging

configure_logging()

# Sample resume text
SAMPLE_RESUME = """
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


def example_regex_strategy():
    """Example: Using the default regex-based extraction strategy."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Regex-Based Extraction (Default)")
    print("="*80)

    # Use the regex strategy directly for all fields
    strategy = RegexExtractionStrategy()

    name = strategy.extract_name(SAMPLE_RESUME)
    email = strategy.extract_email(SAMPLE_RESUME)
    skills = strategy.extract_skills(SAMPLE_RESUME)

    print(f"Name:  {name}")
    print(f"Email: {email}")
    print(f"Skills: {', '.join(skills)}")
    print(f"Total skills found: {len(skills)}")


def example_explicit_regex_strategy():
    """Example: Explicitly using regex strategy."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Explicit Regex Strategy")
    print("="*80)

    regex_strategy = RegexExtractionStrategy()

    name = regex_strategy.extract_name(SAMPLE_RESUME)
    email = regex_strategy.extract_email(SAMPLE_RESUME)
    skills = regex_strategy.extract_skills(SAMPLE_RESUME)

    print(f"Name:  {name}")
    print(f"Email: {email}")
    print(f"Skills: {', '.join(skills)}")


def example_ner_strategy():
    """Example: Using NER-based extraction strategy (placeholder)."""
    print("\n" + "="*80)
    print("EXAMPLE 3: NER-Based Extraction (Placeholder)")
    print("="*80)
    print("NOTE: NER extraction is not yet implemented in this version.")
    print("To implement, install spaCy and add model loading.")
    print()

    ner_strategy = NERExtractionStrategy()

    name = ner_strategy.extract_name(SAMPLE_RESUME)
    email = ner_strategy.extract_email(SAMPLE_RESUME)
    skills = ner_strategy.extract_skills(SAMPLE_RESUME)

    print(f"Name:  {name}")
    print(f"Email: {email}")
    print(f"Skills: {skills}")
    print("\nImplementation TODO: Replace with actual spaCy NER model")


def example_llm_strategy():
    """Example: Using LLM-based extraction strategy with Google Gemini."""
    print("\n" + "="*80)
    print("EXAMPLE 4: LLM-Based Extraction (Google Gemini)")
    print("="*80)
    print("NOTE: Requires GOOGLE_API_KEY environment variable or api_key parameter.")
    print("Install: pip install google-generativeai")
    print()

    # Example 1: Using environment variable
    try:
        llm_strategy = LLMExtractionStrategy(model_name="gemini-3-flash-preview")

        name = llm_strategy.extract_name(SAMPLE_RESUME)
        email = llm_strategy.extract_email(SAMPLE_RESUME)
        skills = llm_strategy.extract_skills(SAMPLE_RESUME)

        print(f"Name (Gemini):   {name}")
        print(f"Email (Gemini):  {email}")
        print(f"Skills (Gemini): {skills}")

    except Exception as e:
        print(f"Gemini extraction failed: {e}")
        print("Make sure GOOGLE_API_KEY is set or pass api_key parameter")

    # Example 2: Using explicit API key
    print("\n--- Alternative: Using explicit API key ---")
    try:
        llm_strategy = LLMExtractionStrategy(
            model_name="gemini-3-flash-preview",
            api_key="AIzaSyBJY8k2Uc0tUOxk7ufm7adUkgo8WHloI10"
        )
        print("To use explicit API key:")
        print('llm_strategy = LLMExtractionStrategy(api_key="your-gemini-api-key")')
        print('name = llm_strategy.extract_name(resume_text)')
        print('email = llm_strategy.extract_email(resume_text)')
        print('skills = llm_strategy.extract_skills(resume_text)')

    except Exception as e:
        print(f"Error: {e}")


def example_framework_with_strategies():
    """Example: Using the ResumeParserFramework with extractor wrappers."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Framework Integration with FieldExtractor Wrappers")
    print("="*80)

    extractors = {
        "name": NameExtractor(),
        "email": EmailExtractor(),
        "skills": SkillsExtractor(),
    }
    resume_extractor = ResumeExtractor(extractors)
    framework = ResumeParserFramework(resume_extractor)

    # Note: In real usage, parse a file:
    # resume_data = framework.parse_resume("path/to/resume.pdf")
    
    # For this example, we extract from text directly
    resume_data = resume_extractor.extract(SAMPLE_RESUME)

    print(f"Extracted Resume Data:")
    print(f"  Name:   {resume_data.name}")
    print(f"  Email:  {resume_data.email}")
    print(f"  Skills: {', '.join(resume_data.skills)}")
    print(f"\nFull data as dict:")
    import json
    print(json.dumps(resume_data.as_dict(), indent=2))


def example_hybrid_strategy():
    """Example: Using different strategies for different fields."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Hybrid Strategy (Different extractors using different strategies)")
    print("="*80)
    print("Note: For production use, you might use regex for email (reliable),")
    print("but NER for names and LLM for skills (more flexible).")
    print()

    regex_strategy = RegexExtractionStrategy()
    ner_strategy = NERExtractionStrategy()
    llm_strategy = LLMExtractionStrategy()

    # Use different strategies for different fields
    name = ner_strategy.extract_name(SAMPLE_RESUME)  # NER for names
    email = regex_strategy.extract_email(SAMPLE_RESUME)  # Regex for emails (reliable)
    skills = llm_strategy.extract_skills(SAMPLE_RESUME)  # LLM for skills (flexible)

    print(f"Name (NER):      {name}")
    print(f"Email (Regex):   {email}")
    print(f"Skills (LLM):    {skills}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("RESUME PARSER - EXTRACTION STRATEGIES EXAMPLES")
    print("="*80)

    example_regex_strategy()
    example_explicit_regex_strategy()
    # example_ner_strategy()
    example_llm_strategy()
    # example_framework_with_strategies()
    # example_hybrid_strategy()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("""
The resume parser now supports pluggable extraction strategies:

1. **RegexExtractionStrategy** (Default)
   - Fast and reliable for well-formatted resumes
   - No external dependencies
   - Good for emails, skills keywords

2. **NERExtractionStrategy** (Placeholder)
   - Uses Named Entity Recognition models (spaCy, transformers)
   - Better for names and entity extraction
   - Requires: pip install spacy

3. **LLMExtractionStrategy** (Google Gemini)
   - Uses Google Gemini models for intelligent extraction
   - Most flexible and accurate for complex text patterns
   - Can handle nuanced extraction tasks
   - Requires: pip install google-generativeai + GOOGLE_API_KEY

You can mix and match strategies for different fields or create custom strategies
by extending the ExtractionStrategy base class.
    """)
