import tempfile
from pathlib import Path

from docling.document_converter import DocumentConverter

PLAIN_TEXT_EXTENSIONS = {".md", ".txt"}
DOCLING_EXTENSIONS = {".pdf", ".docx", ".pptx", ".html", ".htm"}
SUPPORTED_EXTENSIONS = PLAIN_TEXT_EXTENSIONS | DOCLING_EXTENSIONS


class ConversionError(Exception):
    pass


# TODO - Maybe add tests for this service, but it would require adding some test files to the repo, which might not be ideal.
# Alternatively, we could mock the DocumentConverter for testing purposes
# Remember that dockling is heavy and can be slow, so we might want to consider that when writing tests for this service.
class ConversionService:
    def __init__(self) -> None:
        self._converter = DocumentConverter()

    def convert_to_markdown(self, file_content: bytes, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ConversionError(
                f"Unsupported format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

        if ext in PLAIN_TEXT_EXTENSIONS:
            return file_content.decode("utf-8")

        return self._convert_with_docling(file_content, filename)

    def _convert_with_docling(self, file_content: bytes, filename: str) -> str:
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = Path(tmp.name)
        try:
            result = self._converter.convert(tmp_path)
            return result.document.export_to_markdown()
        except Exception as exc:
            raise ConversionError(f"Conversion failed for '{filename}': {exc}") from exc
        finally:
            tmp_path.unlink(missing_ok=True)
