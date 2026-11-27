// Document formatting and statistics helpers for Document Ingestion

export function formatUploadDate(dateVal) {
  if (!dateVal || dateVal === 'Unknown' || dateVal === 'None' || dateVal === 'null') return null;
  try {
    const d = new Date(dateVal);
    if (isNaN(d.getTime())) return null;
    return d.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return null;
  }
}

export function formatFileSize(bytes) {
  if (typeof bytes !== 'number' || isNaN(bytes) || bytes <= 0) return null;
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export function computeDocumentStats(res) {
  const docsList = Array.isArray(res) ? res : (res?.documents || []);
  const totalChunks = typeof res?.total_chunks === 'number'
    ? res.total_chunks
    : docsList.reduce((acc, d) => acc + (d.chunk_count || 0), 0);
  const totalDocuments = typeof res?.total_documents === 'number'
    ? res.total_documents
    : docsList.length;

  return {
    documents: docsList,
    totalDocuments,
    totalChunks,
  };
}
