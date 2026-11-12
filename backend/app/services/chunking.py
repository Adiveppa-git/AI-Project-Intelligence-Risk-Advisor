from uuid import NAMESPACE_URL, uuid5

from app.models.rag import DocumentChunk


class DocumentChunkingService:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: dict) -> list[DocumentChunk]:
        text = str(document.get("text", ""))
        document_id = str(document.get("document_id", ""))
        if not text.strip() or not document_id:
            return []

        base_metadata = {
            key: value
            for key, value in document.items()
            if key not in {"text", "document_id"}
        }
        chunks: list[DocumentChunk] = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                end = self._find_boundary(text, start, end)

            chunk_text = text[start:end].strip()
            if chunk_text:
                index = len(chunks)
                chunk_id = str(uuid5(NAMESPACE_URL, f"{document_id}:{index}"))
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        chunk_index=index,
                        text=chunk_text,
                        metadata={
                            **base_metadata,
                            "start_char": start,
                            "end_char": end,
                        },
                    )
                )

            if end >= len(text):
                break

            next_start = max(start + 1, end - self.chunk_overlap)
            if self.chunk_overlap:
                next_start = self._next_word_boundary(text, next_start, end)
            if next_start <= start or next_start >= end:
                next_start = end
            start = next_start
        return chunks

    def _find_boundary(self, text: str, start: int, target_end: int) -> int:
        minimum_end = start + max(1, int(self.chunk_size * 0.6))
        window = text[minimum_end:target_end]
        boundary = max(
            window.rfind("\n\n"),
            window.rfind("\n"),
            window.rfind(". "),
            window.rfind("? "),
            window.rfind("! "),
            window.rfind(" "),
        )
        if boundary < 0:
            return target_end
        boundary_text = window[boundary : boundary + 2]
        return minimum_end + boundary + (2 if boundary_text in {". ", "? ", "! ", "\n\n"} else 1)

    @staticmethod
    def _next_word_boundary(text: str, start: int, end: int) -> int:
        while start < end and not text[start - 1 : start].isspace() and not text[start].isspace():
            start += 1
        while start < end and text[start].isspace():
            start += 1
        return start
