# Resume Parser - OOP Architecture

A modular, extensible resume parsing framework using object-oriented design patterns. The codebase demonstrates the **Strategy Pattern**, **Wrapper/Adapter Pattern**, and **Factory Pattern** for flexible field extraction from resume text.

## Overview

The Resume Parser extracts key information (name, email, skills) from resume documents (PDF, DOCX, DOC) using pluggable extraction strategies. The architecture allows easy switching between extraction methods without changing core logic.

## Architecture & OOP Design

### Core Design Patterns

1. **Strategy Pattern** (`ExtractionStrategy` and subclasses)
   - Defines a family of extraction algorithms (Regex, NER, LLM)
   - Allows runtime selection of extraction method
   - Promotes open/closed principle

2. **Wrapper/Adapter Pattern** (`FieldExtractor` and subclasses)
   - Wraps extraction strategies into field-specific extractors
   - Provides consistent interface for extracting individual fields
   - Decouples strategy selection from field extraction

3. **Composition** (`ResumeExtractor`)
   - Orchestrates multiple field extractors
   - Returns structured resume data
   - Handles errors and logging

4. **Template Method** (`ResumeParserFramework`)
   - Handles file parsing and orchestration
   - Delegates field extraction to `ResumeExtractor`

## Core Components

### 1. Extraction Strategies (`extractors/strategies.py`)

**Base Class: `ExtractionStrategy`**
```python
class ExtractionStrategy(ABC):
    @abstractmethod
    def extract_name(self, text: str) -> Optional[str]: ...
    @abstractmethod
    def extract_email(self, text: str) -> Optional[str]: ...
    @abstractmethod
    def extract_skills(self, text: str) -> List[str]: ...
```

**Implementations:**

- **`RegexExtractionStrategy`** (Fallback when LLMExtractionStrategy raises exemption )
  - Fast, pattern-based extraction using regular expressions
  - No external dependencies
  - Good for well-formatted resumes
  - Skills matched against predefined keyword list

- **`NERExtractionStrategy`** (Placeholder)
  - Named Entity Recognition approach
  - Intended for spaCy/transformer models
  - Better entity recognition capabilities
  - Not yet implemented

- **`LLMExtractionStrategy`** (Default-Google Gemini)
  - Uses Google Gemini API for intelligent extraction
  - Makes single API call to extract all fields via `extract_all()`
  - **Smart Caching**: Results cached by text hash; subsequent calls reuse cached result (e.g., when extracting name, email, skills from same resume, only 1 API call is made)
  - Falls back to `RegexExtractionStrategy` when LLM fails
  - Supports custom models and API keys

### 2. Field Extractors (`extractors/`)

**Base Class: `FieldExtractor`**
```python
class FieldExtractor(ABC):
    def __init__(self, strategy: Optional[ExtractionStrategy] = None):
        self.strategy = strategy or RegexExtractionStrategy()
    
    @abstractmethod
    def extract(self, text: str) -> Any: ...
```

**Implementations:**

- **`NameExtractor`** - Extracts candidate name using configured strategy
- **`EmailExtractor`** - Extracts email address using configured strategy
- **`SkillsExtractor`** - Extracts technical skills list using configured strategy

**Purpose:** Wraps strategies to provide field-specific interfaces and logging.

### 3. Resume Extractor (`core/resume_extractor.py`)

```python
class ResumeExtractor:
    def __init__(self, extractors: Dict[str, FieldExtractor]):
        self.extractors = extractors
    
    def extract(self, text: str) -> ResumeData:
        # Orchestrates field extractors and returns structured data
```

Orchestrates multiple field extractors and returns `ResumeData` with extracted information.

### 4. Resume Data Model (`models/resume_data.py`)

```python
@dataclass
class ResumeData:
    name: str = ""
    email: str = ""
    skills: List[str] = field(default_factory=list)
    
    def as_dict(self) -> dict: ...
```

Immutable data class for extracted resume information.

### 5. Framework (`core/framework.py`)

```python
class ResumeParserFramework:
    def parse_resume(self, file_path: str) -> ResumeData:
        # 1. Detect file type and select parser
        # 2. Extract text using appropriate parser (PDF/DOCX)
        # 3. Delegate to ResumeExtractor for field extraction
```

High-level orchestrator that handles file parsing and text extraction.

## Testing & Usage

Refer to `SETUP_GUIDE.md` sections:
1. Running the Application
2. Running Tests
3. Explore extraction strategies

## Features

## LLM Caching - Performance & Cost Optimization

The `LLMExtractionStrategy` includes **smart result caching** to minimize API calls and costs:

### How It Works

1. Results are cached by resume text hash
2. **First call** to any extraction method (name, email, or skills) triggers the Gemini API
3. **Subsequent calls** on the same resume text reuse the cached result
4. No code changes needed - caching is transparent

### Example: Reducing API Calls from 3 to 1

```python
from resume_parser.extractors import NameExtractor, EmailExtractor, SkillsExtractor
from resume_parser.extractors.strategies import LLMExtractionStrategy

resume_text = "Jane Smith\nEmail: jane@example.com\nSkills: Python, Docker"

llm_strategy = LLMExtractionStrategy(api_key="your-key")
name_extractor = NameExtractor(strategy=llm_strategy)
email_extractor = EmailExtractor(strategy=llm_strategy)
skills_extractor = SkillsExtractor(strategy=llm_strategy)

# Only 1 API call total (triggered by first extraction)
name = name_extractor.extract(resume_text)       # ← API call here
email = email_extractor.extract(resume_text)     # ← Uses cached result
skills = skills_extractor.extract(resume_text)   # ← Uses cached result
```

**Impact:**
- Reduces Gemini API calls from 3 to 1 per resume
- Significant cost savings when processing multiple extractions per resume
- Same-resume subsequent calls have ~0ms latency (no network delay)

## Logging

Logs are automatically saved to `logs/resume_parser.log` when using `configure_logging()`.

**Log Locations:**
- Console: stdout (all levels)
- File: `logs/resume_parser.log` (all levels)

**Log Format:**
```
2026-04-05 10:30:15,123 [INFO] resume_parser.core.resume_extractor - Starting resume extraction with extractors: {'name': 'NameExtractor', 'email': 'EmailExtractor', 'skills': 'SkillsExtractor'}
```

## OOP Principles Applied

| Principle | Implementation |
|-----------|-----------------|
| **Abstraction** | `ExtractionStrategy` and `FieldExtractor` abstract base classes |
| **Encapsulation** | Private methods (`_call_gemini`, `_fallback_extract`) |
| **Inheritance** | Concrete strategies and extractors extend base classes |
| **Polymorphism** | Runtime strategy selection via strategy pattern |
| **Composition** | `ResumeExtractor` composes multiple field extractors |
| **Single Responsibility** | Each class has one reason to change |
| **Open/Closed** | Open for extension (new strategies), closed for modification |
| **Dependency Inversion** | Depend on abstractions, not concrete implementations |

## File Structure

```

├── core/
│   ├── framework.py          # ResumeParserFramework (orchestrator)
│   ├── resume_extractor.py   # ResumeExtractor (field extraction)
│   └── parser_factory.py      # File type detection
│   └── resume_extractor.py      # Orchestrates multiple field extractors
├── extractors/
│   ├── strategies.py          # ExtractionStrategy implementations
│   ├── base.py               # FieldExtractor abstract class
│   ├── name_extractor.py     # NameExtractor wrapper
│   ├── email_extractor.py    # EmailExtractor wrapper
│   └── skills_extractor.py   # SkillsExtractor wrapper
├── models/
│   └── resume_data.py         # ResumeData dataclass
├── parsers/
│   ├── pdf_parser.py          # PDF text extraction
│   └── word_parser.py         # DOCX/DOC text extraction
│   └── base.py                # BaseParser abstract class
├── utils/
│   └── logger.py              # Logging configuration
├── tests/                     # Test suite
├── main.py                    # CLI entry point
├── run_tests.py               # tests entry point
├── example_strategies.py      # Explore extraction strategies
├── README.md                  # This file
└── requirements.txt           # Dependencies
└── requirements-test.txt      # Test Dependencies
```

## FUTURE ENHANCEMENTS

1. **LLM Model Router Class** ⭐ Next Priority
   - Create `LLMRouter` to support multiple LLM providers (Gemini, GPT-4, Claude)
   - Unified interface for switching models without changing extractors
   - Example:
     ```python
     llm = LLMRouter.create("gemini", api_key="...")  # or "gpt4", "claude"
     strategy = LLMExtractionStrategy(llm=llm)
     ```

2. **Additional Extraction Methods**
   - Deep Learning models for entity extraction
   - Rule-based extraction with configurable patterns
   - Hybrid approaches combining multiple strategies

3. **Performance Improvements**
   - Batch processing for multiple resumes
   - Async API calls for concurrent processing
   - Cache clearing strategy for long-running applications

4. **Enhanced Testing**
   - Implement future feature tests
