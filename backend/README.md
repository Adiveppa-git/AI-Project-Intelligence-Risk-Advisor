# Backend: Document Ingestion and RAG Retrieval

This Python backend implements document upload and text extraction, plus a local RAG foundation for chunking, sentence embeddings, persistent vector indexing, and semantic retrieval. It does not generate AI answers and does not implement AI agents, forecasting, project-health scoring, or a frontend.

## Requirements

- Python 3.10 or later
- Dependencies listed in `requirements.txt`

## Install

From the project root:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

## Run the API

From the project root:

```powershell
backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload
```

The service is available at `http://127.0.0.1:8000`. Interactive API documentation is at `http://127.0.0.1:8000/docs`; health check is `http://127.0.0.1:8000/health`.

## Upload a document (extract text only)

Use the `POST /api/documents/upload` endpoint with a multipart form field named `file`. Supported formats are PDF, DOCX, CSV, and UTF-8 TXT. For example:

```powershell
curl.exe -F "file=@C:\path\to\meeting-notes.txt" http://127.0.0.1:8000/api/documents/upload
```

The successful response includes a generated document ID, safe original filename, detected supported type, byte size, extracted text, and UTC upload timestamp. Uploads are limited to 10 MiB. No uploaded files are persisted by this milestone implementation.

## Index and search documents

- `POST /api/rag/index`: upload a supported file, extract and chunk its text, generate sentence-transformer embeddings, and persist the chunks in ChromaDB.
- `POST /api/rag/search`: submit JSON such as `{"query":"What might delay the release?","top_k":5}` to retrieve semantically similar chunks. The response contains source text, metadata, distance, and similarity; no AI answer is generated.
- `GET /api/rag/status`: inspect the persistent collection and embedding model status.

The default embedding model is `sentence-transformers/all-MiniLM-L6-v2`. Its model files are downloaded the first time indexing or searching is used, unless cached locally. Vectors are stored persistently in `backend/data/chroma/`, which is ignored by Git. See [Step 4 RAG Pipeline](../docs/STEP4_RAG_PIPELINE.md) for chunking, configuration, response details, and limitations.

Optional settings: `RAG_CHUNK_SIZE` (default 1000), `RAG_CHUNK_OVERLAP` (default 150), `RAG_EMBEDDING_MODEL`, `RAG_VECTOR_DB_PATH`, and `RAG_COLLECTION_NAME`.

## Run tests

From the project root:

```powershell
backend\.venv\Scripts\python -m pytest backend\tests -q
```

Tests create small synthetic PDF and DOCX documents in memory and use non-sensitive sample text. They cover ingestion, RAG chunking, real model embeddings, persistent ChromaDB indexing, semantic retrieval, re-indexing, and empty-query behavior. The first RAG integration run needs internet access to download the model unless it is already cached.
