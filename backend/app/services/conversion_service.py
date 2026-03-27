from pathlib import Path


SUPPORTED_EXTENSIONS = {".md", ".txt"}


class ConversionError(Exception):
    pass


class ConversionService:
    def convert_to_markdown(self, file_content: bytes, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ConversionError(
                f"Unsupported format '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
        return file_content.decode("utf-8")
