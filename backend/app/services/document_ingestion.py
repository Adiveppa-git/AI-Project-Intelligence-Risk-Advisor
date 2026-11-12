import csv
import io
import zipfile
from datetime import datetime, timezone
from pathlib import PurePath
from uuid import uuid4

import pymupdf as fitz
from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from lxml.etree import XMLSyntaxError

from app.models.document import IngestedDocument


class DocumentIngestionError(ValueError):
    """A user-provided document is unsupported, invalid, or has no text."""


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".csv", ".txt"}
DEFAULT_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024


class DocumentIngestionService:
    def __init__(self, max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES) -> None:
        if max_file_size_bytes <= 0:
            raise ValueError("max_file_size_bytes must be positive")
        self.max_file_size_bytes = max_file_size_bytes

    def ingest(self, filename: str | None, content: bytes) -> IngestedDocument:
        safe_filename = PurePath(filename or "").name
        extension = PurePath(safe_filename).suffix.lower()
        if not safe_filename or extension not in SUPPORTED_EXTENSIONS:
            raise DocumentIngestionError(
                "Unsupported file type. Upload a PDF, DOCX, CSV, or TXT file."
            )
        if not content:
            raise DocumentIngestionError("The uploaded file is empty.")
        if len(content) > self.max_file_size_bytes:
            raise DocumentIngestionError(
                f"File exceeds the {self.max_file_size_bytes}-byte size limit."
            )

        text = self._extract(extension, content)
        if not text.strip():
            raise DocumentIngestionError(
                "The document contains no extractable text."
            )

        return IngestedDocument(
            document_id=str(uuid4()),
            filename=safe_filename,
            file_type=extension.lstrip("."),
            file_size_bytes=len(content),
            text=text,
            uploaded_at=datetime.now(timezone.utc),
        )

    def _extract(self, extension: str, content: bytes) -> str:
        if extension == ".pdf":
            return self._extract_pdf(content)
        if extension == ".docx":
            return self._extract_docx(content)
        if extension == ".csv":
            return self._extract_csv(content)
        return self._extract_txt(content)

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        if not content.startswith(b"%PDF-"):
            raise DocumentIngestionError(
                "The file extension is PDF, but the content is not a PDF document."
            )
        try:
            with fitz.open(stream=content, filetype="pdf") as pdf:
                text = "\n".join(page.get_text() for page in pdf)
        except (fitz.FileDataError, fitz.EmptyFileError, ValueError) as exc:
            raise DocumentIngestionError("The PDF document is invalid or unreadable.") from exc
        return text.strip()

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if "[Content_Types].xml" not in archive.namelist() or "word/document.xml" not in archive.namelist():
                    raise DocumentIngestionError(
                        "The file extension is DOCX, but the content is not a valid Word document."
                    )
                if sum(info.file_size for info in archive.infolist()) > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise DocumentIngestionError(
                        "The DOCX document expands beyond the allowed processing limit."
                    )
            document = Document(io.BytesIO(content))
        except DocumentIngestionError:
            raise
        except (
            zipfile.BadZipFile,
            KeyError,
            ValueError,
            OSError,
            RuntimeError,
            PackageNotFoundError,
            XMLSyntaxError,
        ) as exc:
            raise DocumentIngestionError(
                "The DOCX document is invalid or unreadable."
            ) from exc

        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(part for part in parts if part.strip()).strip()

    @staticmethod
    def _decode_text(content: bytes) -> str:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise DocumentIngestionError(
                "The document must contain valid UTF-8 text."
            ) from exc
        if "\x00" in text:
            raise DocumentIngestionError("The document contains invalid binary data.")
        return text

    def _extract_csv(self, content: bytes) -> str:
        raw_text = self._decode_text(content)
        try:
            rows = list(csv.reader(io.StringIO(raw_text, newline=""), strict=True))
        except csv.Error as exc:
            raise DocumentIngestionError("The CSV document is malformed.") from exc
        rows = [row for row in rows if any(cell.strip() for cell in row)]
        if not rows:
            return ""

        header = rows[0]
        if len(rows) == 1:
            return " | ".join(cell.strip() for cell in header)
        lines = []
        for row_number, row in enumerate(rows[1:], start=1):
            fields = [
                f"{header[index].strip() if index < len(header) and header[index].strip() else f'Column {index + 1}'}: {value.strip()}"
                for index, value in enumerate(row)
            ]
            lines.append(f"Row {row_number}: " + "; ".join(fields))
        return "\n".join(lines)

    def _extract_txt(self, content: bytes) -> str:
        return self._decode_text(content).strip()
