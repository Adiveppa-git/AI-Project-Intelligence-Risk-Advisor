# Step 3: Document Ingestion Module

## Implementation overview

The backend is a small FastAPI application under `backend/`. A reusable `DocumentIngestionService` validates and extracts text in memory; the upload endpoint returns structured metadata and extracted text. Uploaded files are not persisted. This step does not implement embeddings, vector storage, chunking, AI agents, risk prediction, or a frontend.

The response model follows the Step 2 document identity and metadata design, with fields needed for this endpoint: document identifier, original safe filename, supported file type, byte size, extracted text, and UTC upload timestamp.

## Supported formats

| Format | Validation and extraction |
|---|---|
| PDF | Requires a PDF signature and parses page text with PyMuPDF. Invalid PDFs are rejected. Image-only/scanned PDFs may yield no text and are rejected; OCR is not included. |
| DOCX | Requires a ZIP-based Word structure including the document XML; extracts paragraphs and table rows using python-docx. |
| CSV | Decodes UTF-8 (optional BOM), parses using Python's CSV reader, and formats records as labeled, human-readable rows. |
| TXT | Decodes UTF-8 (optional BOM), rejects binary NULs and invalid UTF-8, and returns trimmed text. |

File extensions identify the intended parser but are not the only check: PDF signatures and DOCX package structure are inspected, and text formats must decode and parse successfully. CSV and TXT are both text formats, so their extension selects how valid text is interpreted.

## API endpoint

`POST /api/documents/upload`

- Request: `multipart/form-data` with a single `file` field.
- Success: `201 Created` with JSON containing `document_id`, `filename`, `file_type`, `file_size_bytes`, `text`, and `uploaded_at`.
- Unsupported extension: `415 Unsupported Media Type`.
- Empty, malformed, undecodable, or no-text document: `422 Unprocessable Entity`.
- File larger than 10 MiB: `413 Request Entity Too Large`.

Example:

```powershell
curl.exe -F "file=@C:\path\to\project-proposal.pdf" http://127.0.0.1:8000/api/documents/upload
```

The upload is read with a bounded `max_size + 1` read, never written to a temporary file, and the request upload handle is closed after reading. The service reduces the filename to its basename and does not use it as a storage path. No document contents are written to disk.

## Installation

Python 3.10 or later is required. From the project root, create a virtual environment and install the backend dependencies:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

## Run the backend

From the project root:

```powershell
backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload
```

The API listens at `http://127.0.0.1:8000`. Interactive API docs are available at `http://127.0.0.1:8000/docs` and the health endpoint at `http://127.0.0.1:8000/health`.

## Run tests

```powershell
backend\.venv\Scripts\python -m pytest backend\tests -q
```

The automated tests generate synthetic PDF/DOCX examples in memory and use non-sensitive text. They cover PDF, DOCX including tables, CSV, TXT, unsupported extensions, empty uploads, invalid documents, mismatched signatures, upload metadata, HTTP errors, and size-limit enforcement.

## Current limitations

- Text extraction only: there is no persistence, document revision management, or project authorization yet.
- Scanned/image-only PDFs require OCR, which is not included.
- CSV/TXT are treated as UTF-8; other encodings must be converted before upload.
- The upload-size limit is 10 MiB by default.
- Chunking, embeddings, vector indexing, RAG retrieval, agents, and dashboards remain future work.
