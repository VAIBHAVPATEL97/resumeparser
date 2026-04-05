import json
import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    logger.warning("python-dotenv not installed. .env file will not be loaded.")

logger = logging.getLogger(__name__)


class ExtractionStrategy(ABC):
    """Abstract base class for extraction strategies."""

    @abstractmethod
    def extract_name(self, text: str) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def extract_email(self, text: str) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def extract_skills(self, text: str) -> List[str]:
        raise NotImplementedError


class LLMExtractionError(Exception):
    """Raised when a Gemini/LLM extraction call fails."""
    pass


class RegexExtractionStrategy(ExtractionStrategy):
    """Regex-based extraction strategy."""

    EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{5,}\d)")
    RESUME_HEADINGS = re.compile(r"\b(resume|curriculum vitae|cv)\b", re.I)
    NAME_LINE_RE = re.compile(r"^[A-Z][a-z]+(?: [A-Z][a-z]+){0,2}$")

    SKILL_KEYWORDS = {
        "aws",
        "azure",
        "bash",
        "bootstrap",
        "c#",
        "c++",
        "css",
        "data analysis",
        "docker",
        "django",
        "excel",
        "fastapi",
        "flask",
        "git",
        "html",
        "java",
        "jenkins",
        "keras",
        "kubernetes",
        "leadership",
        "linux",
        "machine learning",
        "mongodb",
        "node.js",
        "nlp",
        "numpy",
        "pandas",
        "postgresql",
        "problem solving",
        "python",
        "react",
        "redis",
        "rest",
        "scikit-learn",
        "sql",
        "sql server",
        "tensorflow",
        "testing",
        "unix",
        "web development",
        "xml",
    }

    def extract_name(self, text: str) -> Optional[str]:
        if not text:
            logger.debug("Empty text received for name extraction")
            return None

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        lines = [line for line in lines if not self.EMAIL_RE.search(line)]
        lines = [line for line in lines if not self.PHONE_RE.search(line)]

        for line in lines[:10]:
            if self.RESUME_HEADINGS.search(line):
                continue
            if 1 < len(line.split()) <= 4 and self.NAME_LINE_RE.match(line):
                logger.debug("Name extracted from line: %s", line)
                return line

        for line in lines[:10]:
            tokens = [token for token in line.split() if token]
            if 1 < len(tokens) <= 4 and all(token[0].isupper() for token in tokens if token):
                logger.debug("Name extracted by fallback rule: %s", line)
                return line

        logger.debug("No name match found in resume text")
        return None

    def extract_email(self, text: str) -> Optional[str]:
        if not text:
            logger.debug("Empty text received for email extraction")
            return None
        match = self.EMAIL_RE.search(text)
        if match:
            email = match.group(0).lower()
            logger.debug("Email extracted: %s", email)
            return email
        logger.debug("No email found")
        return None

    def extract_skills(self, text: str) -> List[str]:
        if not text:
            logger.debug("Empty text received for skills extraction")
            return []

        normalized = text.lower()
        found = set()
        for skill in self.SKILL_KEYWORDS:
            pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
            if re.search(pattern, normalized):
                found.add(skill)

        if not found:
            logger.debug("No skills identified in resume text")
            return []

        skills = sorted(found)
        logger.debug("Skills extracted: %s", skills)
        return skills


class NERExtractionStrategy(ExtractionStrategy):
    """Named Entity Recognition (NER) based extraction strategy.
    
    Placeholder for NER-based extraction using libraries like spaCy or transformers.
    """

    def __init__(self):
        logger.info("NERExtractionStrategy initialized (placeholder implementation)")
        # TODO: Initialize NER model (e.g., spacy.load('en_core_web_sm'))

    def extract_name(self, text: str) -> Optional[str]:
        if not text:
            logger.debug("Empty text received for name extraction")
            return None

        logger.debug("NER-based name extraction not yet implemented, returning None")
        # TODO: Use NER model to extract PERSON entity
        return None

    def extract_email(self, text: str) -> Optional[str]:
        if not text:
            logger.debug("Empty text received for email extraction")
            return None

        logger.debug("NER-based email extraction not yet implemented, returning None")
        # TODO: Use EMAIL pattern or custom NER
        return None

    def extract_skills(self, text: str) -> List[str]:
        if not text:
            logger.debug("Empty text received for skills extraction")
            return []

        logger.debug("NER-based skills extraction not yet implemented, returning empty list")
        # TODO: Use skill entity recognition or knowledge base
        return []


class LLMExtractionStrategy(ExtractionStrategy):
    """Large Language Model (LLM) based extraction strategy using Google Gemini."""
    # TODO: IN FUTURE, IMPLEMENT MODEL CLASS THAT CAN SUPPORT DIFFERENT LLMS (GEMINI, GPT-4, ETC) WITH A UNIFIED INTERFACE SO WE CAN SWITCH MODELS EASILY WITHOUT CHANGING THE EXTRACTORS
    
    def __init__(self, model_name: str = None, api_key: Optional[str] = None):
        # Load .env file if available
        if HAS_DOTENV:
            load_dotenv()
        
        self.model_name = model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-3-flash-preview")
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
        self._client = None
        self._cache: Dict[int, Dict] = {}  # Cache extraction results by text hash

        if not self.api_key:
            logger.warning("No Gemini API key found. Pass api_key or set GEMINI_API_KEY/GOOGLE_API_KEY environment variable.")

        try:
            from google import genai

            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
                logger.info("LLMExtractionStrategy initialized with Gemini model: %s", model_name)
            else:
                logger.warning("Gemini client not initialized due to missing API key.")

        except ImportError as e:
            logger.error("google-genai package not installed: %s", e)
            raise ImportError("Install google-genai: pip install google-genai") from e
        except Exception as e:
            logger.error("Failed to initialize Gemini client: %s", e)
            raise RuntimeError(f"Gemini initialization failed: {e}") from e

    def _call_gemini(self, prompt: str, max_tokens: int = 300) -> Optional[str]:
        """Call Gemini API with the given prompt."""
        if not self._client:
            logger.warning("Gemini client not initialized, cannot extract")
            return None

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            if not response or not response.text:
                logger.debug("Gemini returned empty response")
                raise LLMExtractionError("Gemini returned empty or invalid response")

            return response.text.strip()

        except Exception as e:
            logger.error("Gemini API call failed: %s", e)
            raise LLMExtractionError("Gemini API call failed") from e

    def extract_all(self, text: str) -> Dict:
        """Extract name, email, and skills in one efficient call."""
        if not text:
            return {}

        text_hash = hash(text)
        
        # Check cache first - reuse result from previous API call
        if text_hash in self._cache:
            logger.debug("Using cached extraction result for resume text")
            return self._cache[text_hash]

        prompt = f"""
        Extract the following from the resume:

        1. Full Name
        2. Email
        3. Technical Skills

        Return ONLY valid JSON with no additional text:
        {{
            "name": "...",
            "email": "...",
            "skills": ["...", "..."]
        }}

        If a field is missing, use null.

        Resume:
        {text}
        """

        result = self._call_gemini(prompt, max_tokens=300)

        if not result:
            return {}

        try:
            data = json.loads(result)
            result_dict = {
                "name": data.get("name"),
                "email": data.get("email"),
                "skills": data.get("skills") or []
            }
            # Cache the result
            self._cache[text_hash] = result_dict
            logger.info("Gemini API call made. Result cached for future field extractions.")
            return result_dict
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response: %s", result)
            return {}

    def extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from resume text."""
        if not text:
            logger.debug("Empty text received for name extraction")
            return None

        data = self.extract_all(text)
        name = data.get("name")
        if name and name.lower() not in ["none", "null", "n/a"]:
            logger.debug("Gemini extracted name: %s", name)
            return name

        logger.debug("No name extracted by Gemini")
        return None

    def extract_email(self, text: str) -> Optional[str]:
        """Extract email from resume text."""
        if not text:
            logger.debug("Empty text received for email extraction")
            return None

        data = self.extract_all(text)
        email = data.get("email")

        if email and email.lower() not in ["none", "null", "n/a"]:
            email_lower = email.strip().lower()
            # Basic email validation
            if "@" in email_lower and "." in email_lower:
                logger.debug("Gemini extracted email: %s", email_lower)
                return email_lower

        logger.debug("No valid email extracted by Gemini")
        return None

    def extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from resume text."""
        if not text:
            logger.debug("Empty text received for skills extraction")
            return []

        data = self.extract_all(text)
        skills = data.get("skills", [])

        if skills and isinstance(skills, list):
            # Remove duplicates and sort
            unique_skills = list(set([s.strip() for s in skills if s and isinstance(s, str)]))
            logger.debug("Gemini extracted skills: %s", unique_skills)
            return sorted(unique_skills)

        logger.debug("No skills extracted by Gemini")
        return []
