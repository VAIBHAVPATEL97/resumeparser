import argparse
import logging
import sys
from pathlib import Path

if __package__ is None:
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from resume_parser.core.framework import ResumeParserFramework
from resume_parser.core.resume_extractor import ResumeExtractor, ResumeParsingError
from resume_parser.extractors import NameExtractor, EmailExtractor, SkillsExtractor
from resume_parser.utils.logger import configure_logging


def build_resume_parser() -> ResumeParserFramework:
    extractors = {
        "name": NameExtractor(),
        "email": EmailExtractor(),
        "skills": SkillsExtractor(),
    }
    return ResumeParserFramework(ResumeExtractor(extractors))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse resume files and extract name, email, and skills."
    )
    parser.add_argument(
        "file_path",
        nargs="?",
        help="Path to the resume file (.pdf, .docx, .doc)",
    )
    parser.add_argument(
        "--file_path",
        "-f",
        dest="file_path",
        help="Path to the resume file (.pdf, .docx, .doc)",
    )
    args = parser.parse_args()
    if not args.file_path:
        parser.error("the following arguments are required: file_path")
    return args


def main() -> int:
    configure_logging()
    args = parse_arguments()
    parser = build_resume_parser()

    try:
        resume_data = parser.parse_resume(str(Path(args.file_path)))
        logging.getLogger(__name__).info("Extracted resume data: %s", resume_data.as_dict())
        print(resume_data.as_dict())
        return 0
    except ResumeParsingError as exc:
        logging.getLogger(__name__).error("Resume parsing failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
