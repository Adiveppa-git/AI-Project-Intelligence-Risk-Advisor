import pytest

from app.services.chunking import DocumentChunkingService


def test_chunking_preserves_document_identity_and_metadata() -> None:
    service = DocumentChunkingService(chunk_size=48, chunk_overlap=8)
    chunks = service.chunk_document(
        {
            "document_id": "doc-123",
            "filename": "proposal.txt",
            "file_type": "txt",
            "text": (
                "The delivery team owns the API migration. "
                "The release milestone is scheduled for September. "
                "Integration testing starts after the database is ready."
            ),
        }
    )
    assert len(chunks) > 1
    assert all(chunk.document_id == "doc-123" for chunk in chunks)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.metadata["filename"] == "proposal.txt" for chunk in chunks)
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
    assert "Integration testing" in "".join(chunk.text for chunk in chunks)


def test_chunk_overlap_repeats_boundary_content() -> None:
    text = "one two three four five six seven eight nine ten"
    chunks = DocumentChunkingService(chunk_size=20, chunk_overlap=8).chunk_document(
        {"document_id": "overlap-doc", "text": text}
    )
    assert len(chunks) > 1
    assert any(
        set(left.text.split()) & set(right.text.split())
        for left, right in zip(chunks, chunks[1:])
    )


def test_short_document_is_one_chunk() -> None:
    chunks = DocumentChunkingService(chunk_size=100, chunk_overlap=20).chunk_document(
        {"document_id": "short-doc", "text": "Short project note."}
    )
    assert len(chunks) == 1
    assert chunks[0].text == "Short project note."


@pytest.mark.parametrize(
    "document",
    [
        {"document_id": "empty", "text": ""},
        {"document_id": "blank", "text": " \n\t"},
        {"document_id": "", "text": "Text without an ID."},
    ],
)
def test_empty_text_or_missing_id_returns_no_chunks(document: dict) -> None:
    assert DocumentChunkingService().chunk_document(document) == []


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [(0, 0), (10, -1), (10, 10)],
)
def test_invalid_chunk_configuration_is_rejected(
    chunk_size: int, overlap: int
) -> None:
    with pytest.raises(ValueError):
        DocumentChunkingService(chunk_size, overlap)
