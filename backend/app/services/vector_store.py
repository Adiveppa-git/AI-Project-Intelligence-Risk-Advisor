import sqlite3
from pathlib import Path

from chromadb.errors import ChromaError

from app.models.rag import DocumentChunk, SearchResult


class VectorStoreError(RuntimeError):
    """The persistent vector store could not complete an operation."""


class ChromaVectorStore:
    def __init__(self, persist_directory: str | Path, collection_name: str = "project_chunks") -> None:
        if not collection_name.replace("_", "").isalnum():
            raise ValueError("collection_name must contain only letters, digits, or underscores")
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self._client = None
        self._collection = None

    @property
    def is_initialized(self) -> bool:
        return self._collection is not None

    def count(self) -> int:
        try:
            return self._get_collection().count()
        except VectorStoreError:
            raise
        except (ChromaError, OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
            raise VectorStoreError("Could not read the ChromaDB collection count.") from exc

    def index_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("Each chunk must have exactly one embedding")
        if not chunks:
            return 0
        if len({chunk.document_id for chunk in chunks}) != 1:
            raise ValueError("All chunks in one indexing operation must share a document_id")

        collection = self._get_collection()
        document_id = chunks[0].document_id
        ids = [chunk.chunk_id for chunk in chunks]
        try:
            old_ids = collection.get(where={"document_id": document_id}, include=[])["ids"]
            collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=[chunk.text for chunk in chunks],
                metadatas=[
                    self._metadata_for(chunk)
                    for chunk in chunks
                ],
            )
            stale_ids = list(set(old_ids) - set(ids))
            if stale_ids:
                collection.delete(ids=stale_ids)
        except (ChromaError, OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
            raise VectorStoreError("Could not index document chunks in ChromaDB.") from exc
        return len(chunks)

    def delete_document(self, document_id: str) -> int:
        collection = self._get_collection()
        try:
            ids = collection.get(where={"document_id": document_id}, include=[])["ids"]
            if ids:
                collection.delete(ids=ids)
            return len(ids)
        except (ChromaError, OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
            raise VectorStoreError(
                f"Could not delete document '{document_id}' from ChromaDB."
            ) from exc

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[SearchResult]:
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")
        try:
            collection = self._get_collection()
            total = collection.count()
            if total == 0:
                return []
            matches = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, total),
                include=["documents", "metadatas", "distances"],
            )
        except (ChromaError, OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
            raise VectorStoreError("Could not search the ChromaDB collection.") from exc

        results: list[SearchResult] = []
        ids = matches["ids"][0]
        documents = matches["documents"][0]
        metadatas = matches["metadatas"][0]
        distances = matches["distances"][0]
        for chunk_id, text, metadata, distance in zip(
            ids, documents, metadatas, distances
        ):
            results.append(
                SearchResult(
                    chunk_id=chunk_id,
                    document_id=str(metadata["document_id"]),
                    chunk_index=int(metadata["chunk_index"]),
                    text=text,
                    metadata={
                        key: value
                        for key, value in metadata.items()
                        if key not in {"document_id", "chunk_index"}
                    },
                    distance=float(distance),
                    similarity=1.0 - float(distance),
                )
            )
        return results

    def _get_collection(self):
        if self._collection is None:
            try:
                import chromadb

                self.persist_directory.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=str(self.persist_directory)
                )
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except (
                ChromaError,
                ImportError,
                OSError,
                RuntimeError,
                ValueError,
                sqlite3.Error,
            ) as exc:
                raise VectorStoreError(
                    f"Could not open persistent ChromaDB storage at "
                    f"'{self.persist_directory}'."
                ) from exc
        return self._collection

    @staticmethod
    def _metadata_for(chunk: DocumentChunk) -> dict[str, str | int | float | bool]:
        metadata: dict[str, str | int | float | bool] = {
            "document_id": chunk.document_id,
            "chunk_index": chunk.chunk_index,
        }
        for key, value in chunk.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                metadata[key] = value
            elif value is not None:
                metadata[key] = str(value)
        return metadata
