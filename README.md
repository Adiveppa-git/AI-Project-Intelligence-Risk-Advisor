# AI Project Intelligence & Risk Advisor

This project turns project proposals, requirements, meeting notes, progress updates, and task lists into grounded project intelligence.

## Milestone 1

- [Step 1 learning notes](docs/STEP1_LEARNING_NOTES.md)
- [Step 2 system architecture](docs/STEP2_SYSTEM_ARCHITECTURE.md)
- [Step 2 data model design](docs/DATA_MODEL_DESIGN.md)
- [Step 3 document ingestion implementation](docs/STEP3_DOCUMENT_INGESTION.md)
- [Step 4 RAG pipeline](docs/STEP4_RAG_PIPELINE.md)
- [Backend setup and usage](backend/README.md)

The current backend supports document upload and text extraction for PDF, DOCX, CSV, and TXT, plus chunking, sentence-transformer embeddings, persistent ChromaDB indexing, and semantic retrieval. It does not generate AI answers; agents, forecasting, project-health scoring, and the frontend are not implemented yet.
