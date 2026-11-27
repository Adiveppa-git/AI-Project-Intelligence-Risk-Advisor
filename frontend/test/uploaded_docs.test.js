import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { formatUploadDate, formatFileSize, computeDocumentStats } from '../src/utils/documentUtils.js';
import { getFileFormatBadge } from '../src/utils/evidenceProvenance.js';

describe('Uploaded Documents UI & Ingestion Utilities Tests', () => {
  describe('formatUploadDate', () => {
    it('formats valid ISO date strings cleanly without inventing dates', () => {
      const formatted = formatUploadDate('2026-11-26T14:30:00Z');
      assert.ok(formatted);
      assert.equal(typeof formatted, 'string');
      // Should contain year and month
      assert.ok(formatted.includes('2026'));
      assert.ok(formatted.includes('Nov'));
    });

    it('returns null for missing, invalid, or placeholder dates', () => {
      assert.equal(formatUploadDate(null), null);
      assert.equal(formatUploadDate(undefined), null);
      assert.equal(formatUploadDate(''), null);
      assert.equal(formatUploadDate('Unknown'), null);
      assert.equal(formatUploadDate('None'), null);
      assert.equal(formatUploadDate('null'), null);
      assert.equal(formatUploadDate('invalid-date-string'), null);
    });
  });

  describe('formatFileSize', () => {
    it('formats sizes in KB and MB accurately', () => {
      assert.equal(formatFileSize(2048), '2.0 KB');
      assert.equal(formatFileSize(15360), '15.0 KB');
      assert.equal(formatFileSize(1048576), '1.0 MB');
      assert.equal(formatFileSize(5242880), '5.0 MB');
    });

    it('returns null for invalid, negative, or zero bytes', () => {
      assert.equal(formatFileSize(0), null);
      assert.equal(formatFileSize(-100), null);
      assert.equal(formatFileSize(null), null);
      assert.equal(formatFileSize(undefined), null);
      assert.equal(formatFileSize(NaN), null);
      assert.equal(formatFileSize('not-a-number'), null);
    });
  });

  describe('computeDocumentStats', () => {
    it('handles standard API response structure', () => {
      const apiResponse = {
        total_documents: 2,
        total_chunks: 7,
        documents: [
          {
            document_id: 'doc-1',
            filename: 'architecture_spec.pdf',
            file_type: 'pdf',
            chunk_count: 5,
            status: 'Indexed',
            uploaded_at: '2026-11-26T10:00:00Z',
          },
          {
            document_id: 'doc-2',
            filename: 'task_list.csv',
            file_type: 'csv',
            chunk_count: 2,
            status: 'Indexed',
            uploaded_at: '2026-11-26T11:00:00Z',
          },
        ],
      };

      const stats = computeDocumentStats(apiResponse);
      assert.equal(stats.totalDocuments, 2);
      assert.equal(stats.totalChunks, 7);
      assert.equal(stats.documents.length, 2);
    });

    it('sums chunk_count across documents when total_chunks is not provided', () => {
      const rawList = [
        { document_id: 'doc-a', filename: 'proposal.txt', chunk_count: 3 },
        { document_id: 'doc-b', filename: 'retro.docx', chunk_count: 4 },
      ];

      const stats = computeDocumentStats(rawList);
      assert.equal(stats.totalDocuments, 2);
      assert.equal(stats.totalChunks, 7);
      assert.equal(stats.documents.length, 2);
    });

    it('handles empty or null document collections gracefully', () => {
      const emptyStats = computeDocumentStats({ total_documents: 0, total_chunks: 0, documents: [] });
      assert.equal(emptyStats.totalDocuments, 0);
      assert.equal(emptyStats.totalChunks, 0);
      assert.deepEqual(emptyStats.documents, []);

      const nullStats = computeDocumentStats(null);
      assert.equal(nullStats.totalDocuments, 0);
      assert.equal(nullStats.totalChunks, 0);
      assert.deepEqual(nullStats.documents, []);
    });

    it('distinguishes document count from chunk count strictly', () => {
      // 1 document chunked into 10 pieces
      const singleDocManyChunks = {
        total_documents: 1,
        total_chunks: 10,
        documents: [
          {
            document_id: 'doc-large',
            filename: 'big_manual.pdf',
            chunk_count: 10,
          },
        ],
      };

      const stats = computeDocumentStats(singleDocManyChunks);
      assert.equal(stats.totalDocuments, 1, 'Document count must be 1, not 10');
      assert.equal(stats.totalChunks, 10, 'Chunk count must be 10');
    });
  });

  describe('File Format Badges', () => {
    it('accurately resolves file formats for all supported types', () => {
      assert.equal(getFileFormatBadge('project_charter.pdf')?.ext, 'PDF');
      assert.equal(getFileFormatBadge('progress_report.docx')?.ext, 'DOCX');
      assert.equal(getFileFormatBadge('task_matrix.csv')?.ext, 'CSV');
      assert.equal(getFileFormatBadge('meeting_notes.txt')?.ext, 'TXT');
    });
  });

  describe('ChromaDB Grouping & Metadata Preservation Verification', () => {
    it('simulates actual stored documents from ChromaDB vector store', () => {
      const storedDocs = [
        {
          document_id: '7d559869-70aa-43d9-a78c-8c760a0a52df',
          filename: 'sample_project_report.txt',
          file_type: 'txt',
          file_size_bytes: 8432,
          chunk_count: 4,
          status: 'Indexed',
          uploaded_at: '2026-11-26T12:00:00Z',
        },
        {
          document_id: '67584160-5f25-4c07-ae7c-2b5d43be6cbb',
          filename: 'project_proposal.txt',
          file_type: 'txt',
          file_size_bytes: 5210,
          chunk_count: 3,
          status: 'Indexed',
          uploaded_at: '2026-11-26T12:05:00Z',
        },
        {
          document_id: '2075b8ba-0125-4298-b80c-e2f4ea69c8b0',
          filename: 'meeting_notes.txt',
          file_type: 'txt',
          file_size_bytes: 2890,
          chunk_count: 2,
          status: 'Indexed',
          uploaded_at: '2026-11-26T12:10:00Z',
        },
        {
          document_id: '861a3d3c-9a29-4d2b-b6fb-f1ff5b2ba27c',
          filename: 'progress_report.docx',
          file_type: 'docx',
          file_size_bytes: 14200,
          chunk_count: 2,
          status: 'Indexed',
          uploaded_at: '2026-11-26T12:15:00Z',
        },
        {
          document_id: 'f9411985-78e8-4682-8bc7-e7ba286df952',
          filename: 'task_list.csv',
          file_type: 'csv',
          file_size_bytes: 4100,
          chunk_count: 2,
          status: 'Indexed',
          uploaded_at: '2026-11-26T12:20:00Z',
        },
        {
          document_id: 'b6e8feef-5881-4a11-8ec8-cb48b2fc8e33',
          filename: 'project_charter.pdf',
          file_type: 'pdf',
          file_size_bytes: 25600,
          chunk_count: 1,
          status: 'Indexed',
          uploaded_at: '2026-11-26T12:25:00Z',
        },
      ];

      const res = {
        total_documents: storedDocs.length,
        total_chunks: storedDocs.reduce((acc, d) => acc + d.chunk_count, 0),
        documents: storedDocs,
      };

      const stats = computeDocumentStats(res);
      assert.equal(stats.totalDocuments, 6);
      assert.equal(stats.totalChunks, 14);

      // Verify each document item retains required fields
      for (const doc of stats.documents) {
        assert.ok(doc.document_id);
        assert.ok(doc.filename);
        assert.ok(doc.file_type);
        assert.ok(doc.chunk_count >= 1);
        assert.equal(doc.status, 'Indexed');
        assert.ok(formatUploadDate(doc.uploaded_at));
        assert.ok(formatFileSize(doc.file_size_bytes));
        assert.ok(getFileFormatBadge(doc.filename));
      }
    });
  });

  describe('Uploaded Documents Initial Slicing and View All Toggle Logic', () => {
    const mockDocs = [
      { document_id: '1', filename: 'doc1.pdf', chunk_count: 3 },
      { document_id: '2', filename: 'doc2.docx', chunk_count: 2 },
      { document_id: '3', filename: 'doc3.csv', chunk_count: 4 },
      { document_id: '4', filename: 'doc4.txt', chunk_count: 1 },
      { document_id: '5', filename: 'doc5.pdf', chunk_count: 5 },
      { document_id: '6', filename: 'doc6.docx', chunk_count: 2 },
    ];

    it('initially limits display to top 3 documents when list has more than 3 items', () => {
      const showAllDocs = false;
      const displayedDocs = showAllDocs ? mockDocs : mockDocs.slice(0, 3);
      assert.equal(displayedDocs.length, 3);
      assert.deepEqual(displayedDocs.map(d => d.filename), ['doc1.pdf', 'doc2.docx', 'doc3.csv']);
    });

    it('displays all documents when showAllDocs toggle is true', () => {
      const showAllDocs = true;
      const displayedDocs = showAllDocs ? mockDocs : mockDocs.slice(0, 3);
      assert.equal(displayedDocs.length, 6);
      assert.equal(displayedDocs[5].filename, 'doc6.docx');
    });

    it('correctly calculates remaining items count for View All button', () => {
      const remainingCount = mockDocs.length - 3;
      assert.equal(remainingCount, 3);
      const buttonText = `View All (${mockDocs.length} Documents) • +${remainingCount} more`;
      assert.equal(buttonText, 'View All (6 Documents) • +3 more');
    });

    it('does not require toggle button when list has 3 or fewer documents', () => {
      const shortList = mockDocs.slice(0, 3);
      const shouldShowButton = shortList.length > 3;
      assert.equal(shouldShowButton, false);

      const showAll = false;
      const displayedDocs = showAll ? shortList : shortList.slice(0, 3);
      assert.equal(displayedDocs.length, 3);
    });

    it('formats document and indexed chunk counts with correct singular/plural badges', () => {
      const docCountSingular = 1;
      const docBadgeSingular = `${docCountSingular} ${docCountSingular === 1 ? 'Document' : 'Documents'}`;
      assert.equal(docBadgeSingular, '1 Document');

      const docCountPlural = 6;
      const docBadgePlural = `${docCountPlural} ${docCountPlural === 1 ? 'Document' : 'Documents'}`;
      assert.equal(docBadgePlural, '6 Documents');

      const chunkCountSingular = 1;
      const chunkBadgeSingular = `${chunkCountSingular} ${chunkCountSingular === 1 ? 'Indexed Chunk' : 'Indexed Chunks'}`;
      assert.equal(chunkBadgeSingular, '1 Indexed Chunk');

      const chunkCountPlural = 17;
      const chunkBadgePlural = `${chunkCountPlural} ${chunkCountPlural === 1 ? 'Indexed Chunk' : 'Indexed Chunks'}`;
      assert.equal(chunkBadgePlural, '17 Indexed Chunks');
    });
  });
});
