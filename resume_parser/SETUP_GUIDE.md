# Resume Parser - Setup Guide

> **Quick Start**: Get the Resume Parser running in under 5 minutes!

This guide provides step-by-step instructions to set up and run the Resume Parser project on your local machine.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Detailed Setup](#detailed-setup)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Prerequisites

### Required Software

- **Python 3.8 or higher** - [Download from python.org](https://python.org)
- **pip** - Python package installer (comes with Python 3.4+)
- **Git** (optional) - For cloning repositories

### Verify Prerequisites

```bash
# Check Python version
python --version
# Should show: Python 3.8.x or higher

# Check pip version
pip --version
# Should show pip version
```

### Git clone

```bash
git clone https://github.com/VAIBHAVPATEL97/resumeparser.git
```

### Open resume_parser folder
Note: This folder structure needs some cleanup.
```bash
cd resumeparser/resume_parser/
```



## Detailed Setup

### 1. Project Directory Structure

Ensure you're in the correct directory:

```
c:\Users\User\Desktop\Interview Assessment\PolicyReporter\resume_parser\
├── core\           # Core framework components
├── extractors\     # Extraction strategies and wrappers
├── models\         # Data models
├── parsers\        # File parsers (PDF, DOCX)
├── tests\          # Test suite
├── utils\          # Utilities (logging, etc.)
├── main.py         # CLI entry point
├── run_tests.py    # Test runner
├── requirements.txt # Dependencies
├── .env.example    # Environment template
└── README.md       # Main documentation
```

### 2. Virtual Environment Setup

#### Using uv (Modern Python Tooling)

```bash
# Ensure you have pip installed
# Install uv (if not already installed)
pip install uv

# Create and activate virtual environment
uv venv policyreporter   

# Activate (same as venv)
# Windows:
# venv\Scripts\activate
# macOS/Linux:
source policyreporter/bin/activate
```

### 3. Install Dependencies

```bash
# Install all required packages
uv pip install -r requirements.txt
uv pip install -r requirements-test.txt
```

### 4. Environment Configuration

#### Set .env File

Open `.env` in your text editor and configure:

```bash
# Required for LLM extraction (optional for basic regex usage)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Optional: Specify which Gemini model to use
GEMINI_MODEL_NAME=gemini-3-flash-preview
```

#### Get Gemini API Key (Optional)

1. Go to [Google AI Studio](https://ai.google.dev/gemini-api/docs/pricing)
2. Create a new API key
3. Copy the key to your `.env` file

**Note**: Without an API key, the parser will use regex extraction (still works well!)

## Running the Application

### Basic Usage

```bash
# Parse a resume file
python main.py -file_path path/to/resume.pdf  

# Examples:
python3 main.py -file_path software-engineer-resume.pdf
python3 main.py -file_path sample_word_resume.docx
```
**Logs from run is saved in current directory `logs` folder**

### Output Format

The parser outputs JSON with extracted information:

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "skills": ["Python", "JavaScript", "AWS", "Docker"]
}
```

### Supported File Types

- **PDF** (.pdf) - Portable Document Format
- **DOCX** (.docx) - Microsoft Word (2007+)
- **DOC** (.doc) - Microsoft Word (legacy)


## Running Tests

### Run All Tests

```bash
# Using the test runner script
python run_tests.py # Note: Ensure run_tests.py is accessible

# Or using pytest directly
python -m pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
python run_tests.py --unit

**Note:** A couple of unit tests will fail as the skills extraction might not match the asserted skills. This is intentional.

# Integration tests only
python run_tests.py --integration

```

### Test Coverage Report

```bash
# Generate coverage report
python run_tests.py --coverage  

# View coverage report
# Open htmlcov/index.html in your browser
```


## Troubleshooting

### Common Issues

#### 1. "Module not found" errors

```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or upgrade pip and reinstall
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Virtual environment not activating

```bash
# Windows: Use correct path
venv\Scripts\activate

# Check if activated (prompt should show (venv))
where python
```

#### 3. API Key not working

```bash
# Check .env file exists and has correct key
type .env

# Test API key loading
python -c "from extractors.strategies import LLMExtractionStrategy; s = LLMExtractionStrategy(); print('API loaded:', bool(s.api_key))"
```

#### 4. File parsing errors

```bash
# Check file exists and is readable
dir "path\to\your\resume.pdf"

# Try with a simple text file first
echo "John Doe\njohn@example.com\nPython, JavaScript" > test_resume.txt
python main.py test_resume.txt
```

### Debug Mode

```bash
# Enable verbose logging
set PYTHONPATH=%CD%
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Your test code here
"
```

## Examples

### Example 1: Parse a PDF Resume

```bash
# Assuming you have a resume.pdf file
python main.py resume.pdf
```

### Example 2: Parse Multiple Files

```bash
# Create a batch script (Windows)
for %f in (*.pdf) do python main.py "%f"

# Or process individually
python main.py resume1.pdf
python main.py resume2.docx
```

### Example 3: Test with Sample Data

```bash
# Create sample resume content
echo "Jane Smith
Senior Python Developer
Email: jane.smith@company.com
Skills: Python, Django, PostgreSQL, AWS, Docker, Kubernetes
Experience: 5+ years in web development" > sample_resume.txt

# Parse it
python main.py sample_resume.txt
```

### Example 4: Using Different Strategies

```python
# test_strategies.py
from resume_parser.extractors.strategies import RegexExtractionStrategy, LLMExtractionStrategy

# Test regex extraction
regex_strategy = RegexExtractionStrategy()
result = regex_strategy.extract_skills("I know Python, JavaScript, and AWS")
print("Regex skills:", result)

# Test LLM extraction (requires API key)
try:
    llm_strategy = LLMExtractionStrategy()
    result = llm_strategy.extract_skills("I know Python, JavaScript, and AWS")
    print("LLM skills:", result)
except Exception as e:
    print("LLM extraction failed:", e)
```

### Example 5: Integration Test

```python
# test_integration.py
from resume_parser.core.framework import ResumeParserFramework
from resume_parser.extractors import NameExtractor, EmailExtractor, SkillsExtractor
from resume_parser.core.resume_extractor import ResumeExtractor

# Create sample resume text
resume_text = """
John Developer
Senior Software Engineer
Email: john.dev@techcorp.com
Phone: (555) 123-4567

Skills: Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL
"""

# Test framework
framework = ResumeParserFramework(
    ResumeExtractor({
        "name": NameExtractor(),
        "email": EmailExtractor(),
        "skills": SkillsExtractor()
    })
)

result = framework.parse_resume_text(resume_text)
print("Extracted data:", result.as_dict())
```

## Next Steps

Once setup is complete:

1. **Explore the Codebase**: Read `README.md` for architecture details
2. **Run Examples**: Try `examples_strategies.py` for different extraction methods
3. **Customize Strategies**: Modify extraction logic in `extractors/strategies.py`
4. **Add Tests**: Write tests for new features in `tests/`
5. **Contribute**: Check the main README for contribution guidelines

## Support

If you encounter issues:

1. Check this troubleshooting section
2. Run the health check script above
3. Check the logs in `logs/resume_parser.log`
4. Review the main `README.md` for detailed documentation
5. Check the test suite: `python run_tests.py`

---

**🎉 Congratulations!** You're now ready to use the Resume Parser. Happy coding!</content>
<parameter name="filePath">c:\Users\User\Desktop\Interview Assessment\PolicyReporter\resume_parser\SETUP_GUIDE.md
