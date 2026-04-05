import logging
from pathlib import Path


from ..parsers.base import FileParserError
from ..parsers.pdf_parser import PDFParser
from ..parsers.word_parser import WordParser

PARSER_MAP = {
    ".pdf": PDFParser,
    ".docx": WordParser,
    ".doc": WordParser,
}


def get_parser(file_path: str):
    extension = Path(file_path).suffix.lower()
    parser_class = PARSER_MAP.get(extension)
    logging.info("Selected parser %s for file %s", parser_class.__name__ if parser_class else "None", file_path)
    if parser_class is None:
        supported = ", ".join(sorted(PARSER_MAP))
        raise FileParserError(
            f"Unsupported file type: {extension}. Supported extensions: {supported}"
        )
    return parser_class()
