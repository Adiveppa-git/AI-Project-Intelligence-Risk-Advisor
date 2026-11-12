import io
import zipfile

import pymupdf as fitz
import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.main import app
from app.services.document_ingestion import (
    DocumentIngestionError,
    DocumentIngestionService,
)

client = TestClient(app)


def make_pdf(text: str = "Project proposal: release in September.") -> bytes:
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text((72, 72), text)
    content = pdf.tobytes()
    pdf.close()
    return content


def make_docx() -> bytes:
    document = Document()
    document.add_paragraph("Sprint review: API integration is complete.")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Task"
    table.cell(0, 1).text = "Owner"
    table.cell(1, 0).text = "Testing"
    table.cell(1, 1).text = "Alex"
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def test_ingest_pdf() -> None:
    result = DocumentIngestionService().ingest("proposal.pdf", make_pdf())
    assert "Project proposal" in result.text
    assert result.file_type == "pdf"
    assert result.file_size_bytes > 0
    assert result.filename == "proposal.pdf"
    assert result.document_id
    assert result.uploaded_at.tzinfo is not None


def test_ingest_docx_paragraphs_and_tables() -> None:
    result = DocumentIngestionService().ingest("notes.docx", make_docx())
    assert "API integration is complete" in result.text
    assert "Task | Owner" in result.text
    assert "Testing | Alex" in result.text


def test_ingest_csv_as_labeled_rows() -> None:
    content = b"Task,Owner,Status\r\nWrite tests,Alex,In progress\r\n"
    result = DocumentIngestionService().ingest("tasks.csv", content)
    assert "Task: Write tests" in result.text
    assert "Owner: Alex" in result.text
    assert "Status: In progress" in result.text


def test_ingest_txt_with_utf8_bom() -> None:
    result = DocumentIngestionService().ingest("update.txt", b"\xef\xbb\xbfSprint 2 is complete.")
    assert result.text == "Sprint 2 is complete."


def test_unsupported_file_type() -> None:
    with pytest.raises(DocumentIngestionError, match="Unsupported file type"):
        DocumentIngestionService().ingest("archive.exe", b"not supported")


def test_empty_file() -> None:
    with pytest.raises(DocumentIngestionError, match="uploaded file is empty"):
        DocumentIngestionService().ingest("empty.txt", b"")


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("bad.pdf", b"%PDF- this is not a valid PDF"),
        ("bad.docx", b"not a zip file"),
        ("bad.txt", b"\xff\xfe"),
        ("bad.csv", b"\xff\xfe"),
    ],
)
def test_invalid_documents(filename: str, content: bytes) -> None:
    with pytest.raises(DocumentIngestionError):
        DocumentIngestionService().ingest(filename, content)


def test_empty_extracted_document() -> None:
    with pytest.raises(DocumentIngestionError, match="no extractable text"):
        DocumentIngestionService().ingest("blank.txt", b" \n\t")


def test_extension_must_match_document_signature() -> None:
    with pytest.raises(DocumentIngestionError, match="not a PDF"):
        DocumentIngestionService().ingest("renamed.pdf", b"plain text")


@pytest.mark.parametrize(
    ("filename", "content", "expected_text"),
    [
        ("proposal.pdf", make_pdf("Project proposal: release in September."), "Project proposal"),
        ("notes.docx", make_docx(), "API integration is complete"),
        ("tasks.csv", b"Task,Owner\r\nWrite tests,Alex\r\n", "Owner: Alex"),
        ("meeting.txt", b"Review API delivery.", "Review API delivery."),
    ],
    ids=["pdf", "docx", "csv", "txt"],
)
def test_upload_endpoint_returns_metadata_and_extracted_text(
    filename: str, content: bytes, expected_text: str
) -> None:
    response = client.post(
        "/api/documents/upload",
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == filename
    assert body["file_type"] == filename.rsplit(".", 1)[1]
    assert expected_text in body["text"]
    assert body["document_id"]
    assert body["uploaded_at"]


@pytest.mark.parametrize(
    ("filename", "content", "expected_status"),
    [
        ("bad.bin", b"binary", 415),
        ("empty.txt", b"", 422),
        ("invalid.pdf", b"not a PDF", 422),
    ],
)
def test_upload_endpoint_reports_validation_errors(
    filename: str, content: bytes, expected_status: int
) -> None:
    response = client.post(
        "/api/documents/upload",
        files={"file": (filename, content, "application/octet-stream")},
    )
    assert response.status_code == expected_status
    assert response.json()["detail"]


def test_upload_endpoint_enforces_size_limit() -> None:
    from app.api.routes import ingestion_service

    original_limit = ingestion_service.max_file_size_bytes
    ingestion_service.max_file_size_bytes = 16
    try:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("large.txt", b"x" * 17, "text/plain")},
        )
    finally:
        ingestion_service.max_file_size_bytes = original_limit
    assert response.status_code == 413
    assert "size limit" in response.json()["detail"]


def test_docx_named_file_requires_docx_structure() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("not-a-docx.xml", "<root />")
    with pytest.raises(DocumentIngestionError, match="not a valid Word document"):
        DocumentIngestionService().ingest("fake.docx", stream.getvalue())


def test_docx_with_malformed_xml_is_rejected() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types>")
        archive.writestr("word/document.xml", "<document>")
    with pytest.raises(DocumentIngestionError, match="invalid or unreadable"):
        DocumentIngestionService().ingest("malformed.docx", stream.getvalue())
