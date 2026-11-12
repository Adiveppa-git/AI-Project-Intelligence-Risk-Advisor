# Step 4: RAG Pipeline

## Overview

The backend now provides a retrieval foundation that connects document ingestion to chunking, local sentence embeddings, persistent vector indexing, and semantic search. It returns matching source passages; it does **not** generate AI answers or implement an assistant, agents, forecasting, scoring, or a frontend.

The existing `POST /api/documents/upload` endpoint remains unchanged and still only extracts text. Use `POST /api/rag/index` when a document should also be chunked, embedded, and persisted in the vector index. Both endpoints reuse the existing `DocumentIngestionService`.

## Chunking strategy

`DocumentChunkingService` splits extracted text into character-bounded passages. It chooses the latest available paragraph, line, sentence, or whitespace boundary within the allowed chunk window, falling back to the configured character limit for long unbroken text. The default maximum is 1,000 characters with a 150-character target overlap; the overlap is adjusted to word boundaries to avoid cutting words, so its exact length can vary. Both values are configurable.

Each chunk has a stable UUID derived from the document ID and chunk index, its index, text, and metadata inherited from the ingested document (including filename, file type, size, and upload time). Character offsets are retained as metadata. Empty text or a missing document ID produces no chunks. Overlap must be smaller than chunk size; invalid settings are rejected.

## Embedding model

The default model is `sentence-transformers/all-MiniLM-L6-v2`. It is a compact, commonly used English sentence-embedding model with 384-dimensional output, suitable for a local CPU-based project prototype. The service normalizes embeddings and uses the same configured model for document passages and user queries, which is required for meaningful vector comparison.

The model is not bundled in the source code. On its first use, `sentence-transformers` downloads the model files from Hugging Face unless they are already in the local cache. Initial internet access is therefore normally required. Later runs can use the cache; an offline environment must pre-populate that cache. The model is CPU-configured for broad local compatibility, though inference speed depends on document volume and hardware.

Embedding failures are surfaced as service-unavailable errors by the API rather than replaced with random or fabricated vectors.

## Vector database

ChromaDB's `PersistentClient` stores chunk text, embeddings, IDs, and metadata on disk. The default collection is `project_chunks` and the default data directory is `backend/data/chroma/`. The directory is local application data and excluded from version control.

The collection uses cosine distance. Re-indexing identical filename and text produces the same document ID; chunk IDs are deterministic by document and chunk index. The index upserts current chunks and removes stale chunks for that document, avoiding duplicate entries when re-indexed. `ChromaVectorStore.delete_document(document_id)` supports document-level removal.

This prototype does not yet include project/tenant IDs or authorization. Do not expose the API to untrusted users or treat the local index as a production multi-tenant store.

## Workflow

### Indexing

1. The index endpoint reads a bounded upload and passes the file to the existing ingestion service.
2. The ingestion service validates and extracts text for PDF, DOCX, CSV, or TXT.
3. The chunker produces source-associated chunks.
4. The embedding service encodes all chunks with the configured sentence-transformer model.
5. ChromaDB persistently upserts vectors, text, and simple metadata.
6. The endpoint returns the ingested document metadata and the number of chunks/vectors stored.

### Retrieval

1. A client submits a natural-language query and optional `top_k`.
2. The same embedding service generates the query vector.
3. ChromaDB finds nearest vectors using cosine distance.
4. The API returns chunk text, document/chunk identifiers, metadata, distance, and cosine similarity (`1 - distance`).

The score is a ranking signal, not a guarantee of factual relevance. Search returns an empty result list when the index is empty. No LLM response is generated.

## API endpoints

### `POST /api/rag/index`

Request: `multipart/form-data` with a `file` field. Supports PDF, DOCX, CSV, and TXT, subject to the existing upload size limit.

Successful response (`201 Created`) includes:

- `document`: document ID, filename, file type, size, extracted text, and upload timestamp.
- `chunks_created` and `vectors_stored`.
- `embedding_model`.

Validation errors return `415` for unsupported types or `422` for invalid/empty documents. Files over the limit return `413`; model or vector-store errors return `503`.

### `POST /api/rag/search`

JSON request:

```json
{
  "query": "What is blocking the release?",
  "top_k": 5
}
```

`query` must contain non-whitespace text and be at most 4,000 characters. `top_k` defaults to 5 and must be between 1 and 20. The response has the original query and a ranked `results` array containing chunk text, IDs, metadata, distance, and similarity. An empty index returns `200` with `results: []`.

### `GET /api/rag/status`

Returns collection name, stored chunk count, configured embedding model, whether it has been loaded in this process, persistent-storage status/path, and check time. This endpoint checks storage but does not force the model to download.

The existing `POST /api/documents/upload` and `GET /health` endpoints remain available.

## Installation and startup

From the project root, install the declared backend dependencies:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

Start the API:

```powershell
backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://127.0.0.1:8000`; OpenAPI documentation is at `http://127.0.0.1:8000/docs`. The first index or search operation may take longer while the model is downloaded and loaded.

## Configuration

Optional environment variables:

| Variable | Default | Description |
|---|---|---|
| `RAG_CHUNK_SIZE` | `1000` | Maximum chunk size in characters. Must be positive. |
| `RAG_CHUNK_OVERLAP` | `150` | Character overlap between chunks. Must be non-negative and smaller than chunk size. |
| `RAG_EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Hugging Face sentence-transformer model ID or local model path. |
| `RAG_VECTOR_DB_PATH` | `backend/data/chroma` | Persistent ChromaDB directory. |
| `RAG_COLLECTION_NAME` | `project_chunks` | ChromaDB collection name. Letters, digits, and underscores only. |

For example, set variables in PowerShell before starting:

```powershell
$env:RAG_CHUNK_SIZE = "1200"
$env:RAG_CHUNK_OVERLAP = "150"
$env:RAG_VECTOR_DB_PATH = "C:\project-data\chroma"
```

The model cache can be pre-populated or redirected using Hugging Face's standard cache environment variables, such as `HF_HOME`.

## Testing

Run all ingestion and RAG tests from the project root:

```powershell
backend\.venv\Scripts\python -m pytest backend\tests -q
```

The suite includes chunk boundaries/overlap/empty inputs and integration tests that use the actual sentence-transformer model and a real temporary persistent ChromaDB collection. The first integration run downloads the model if it is not cached. Integration coverage checks vector dimensions and normalization, semantic retrieval, multiple documents, duplicate indexing, deletion, empty searches, and reopening the persistent database.

**Verified in this workspace:** `37 passed, 1 warning` with the command above. The warning is a Starlette/AnyIO deprecation from the test client. `pip check` reported no broken requirements. The integration tests used the actual 384-dimensional model and a persistent ChromaDB collection.

The live API check returned HTTP 200 from `/health`; the original upload route and all four RAG indexing formats returned HTTP 201. Semantic search placed the expected PDF passage first (cosine similarity `0.7747`), and the status route reported four indexed chunks. After stopping the server, a fresh Python process reopened the persistent collection and still counted all four chunks. Synthetic live-verification data was then removed.

## Known limitations

- Search retrieves relevant passages only; there is no LLM answer generation.
- No multi-agent orchestration, risk prediction, project health scoring, or frontend is included.
- The default embedding model is English-oriented and may not suit multilingual project documents.
- OCR is not included; scanned PDFs without extractable text are rejected by Step 3 ingestion.
- The model requires a first-time download unless a local copy is configured.
- The first request that loads/downloads the model can take longer than a typical HTTP client timeout; subsequent requests use the in-process model.
- The local vector store has no authentication, project isolation, retention policy, or concurrent multi-process coordination.
- The API does not persist original uploaded files; it persists extracted chunk text and vectors in ChromaDB.
- Changing the embedding model or vector dimensions requires rebuilding the collection with compatible embeddings.
