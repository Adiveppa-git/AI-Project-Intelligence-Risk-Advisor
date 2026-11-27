// Provenance & filename resolution utilities for Evidence Modal

// Helper to determine if a string is a genuine filename (not 'Unknown', empty, or generic agent label)
export function isValidFilename(val) {
  if (!val || typeof val !== 'string') return false;
  const trimmed = val.trim();
  if (!trimmed) return false;
  const lower = trimmed.toLowerCase();
  if (
    lower === 'unknown' ||
    lower === 'not specified' ||
    lower === 'document evidence' ||
    lower === 'source reference' ||
    lower === 'null' ||
    lower === 'undefined' ||
    lower === 'blocker agent' ||
    lower === 'scope agent' ||
    lower === 'risk agent' ||
    lower === 'multi-agent orchestrator'
  ) {
    return false;
  }
  return true;
}

// Extract format badge details for PDF, DOCX, CSV, TXT
export function getFileFormatBadge(filename) {
  if (!filename || typeof filename !== 'string') return null;
  const lower = filename.toLowerCase();
  if (lower.endsWith('.pdf')) {
    return { ext: 'PDF', color: 'bg-rose-100 text-rose-700 border-rose-200' };
  }
  if (lower.endsWith('.docx') || lower.endsWith('.doc')) {
    return { ext: 'DOCX', color: 'bg-blue-100 text-blue-700 border-blue-200' };
  }
  if (lower.endsWith('.csv')) {
    return { ext: 'CSV', color: 'bg-emerald-100 text-emerald-700 border-emerald-200' };
  }
  if (lower.endsWith('.txt')) {
    return { ext: 'TXT', color: 'bg-amber-100 text-amber-800 border-amber-200' };
  }
  return null;
}

// Resolve best source filename from evidence item or modal fallback
export function resolveSourceFilename(ev, fallbackFilename = null, modalSource = null) {
  if (typeof ev === 'string') {
    if (isValidFilename(fallbackFilename)) return fallbackFilename.trim();
    if (isValidFilename(modalSource)) return modalSource.trim();
    return 'Source filename unavailable';
  }

  const candidates = [
    ev?.filename,
    ev?.source_document,
    ev?.document_name,
    ev?.file_name,
    ev?.source,
    ev?.metadata?.filename,
    ev?.metadata?.source_document,
    ev?.metadata?.document_name,
    ev?.metadata?.source,
    fallbackFilename,
    modalSource,
    ev?.document_id,
  ];

  for (const cand of candidates) {
    if (isValidFilename(cand)) {
      return cand.trim();
    }
  }

  return 'Source filename unavailable';
}
