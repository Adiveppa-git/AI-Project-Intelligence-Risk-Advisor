import math
from collections.abc import Sequence

from requests.exceptions import RequestException

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingError(RuntimeError):
    """The configured embedding model could not encode input text."""


class SentenceTransformerEmbeddingService:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        if not model_name.strip():
            raise ValueError("model_name cannot be empty")
        self.model_name = model_name
        self._model = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._encode(texts)

    def embed_query(self, query: str) -> list[float]:
        if not query.strip():
            raise ValueError("query cannot be empty")
        return self._encode([query])[0]

    def _encode(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("embedding input text cannot be empty")
        try:
            model = self._load_model()
            vectors = model.encode(
                list(texts),
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            result = [[float(value) for value in vector] for vector in vectors]
        except (ImportError, OSError, RequestException, RuntimeError, TypeError, ValueError) as exc:
            raise EmbeddingError(
                f"Could not generate embeddings with model '{self.model_name}'."
            ) from exc

        if len(result) != len(texts) or any(
            not vector or any(not math.isfinite(value) for value in vector)
            for vector in result
        ):
            raise EmbeddingError("The embedding model returned invalid vectors.")
        dimensions = len(result[0])
        if any(len(vector) != dimensions for vector in result):
            raise EmbeddingError("The embedding model returned inconsistent dimensions.")
        return result

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name, device="cpu")
            except (ImportError, OSError, RequestException, RuntimeError, ValueError) as exc:
                raise EmbeddingError(
                    f"Could not load embedding model '{self.model_name}'. "
                    "Check the model name, network access for the initial download, "
                    "and the local model cache."
                ) from exc
        return self._model
