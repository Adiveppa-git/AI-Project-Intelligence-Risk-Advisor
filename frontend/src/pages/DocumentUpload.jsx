import React, { useState, useEffect, useCallback } from 'react';
import { 
  Upload, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Sparkles, 
  Copy, 
  Check, 
  Database, 
  FileCheck,
  RefreshCw,
  FolderOpen
} from 'lucide-react';
import Badge from '../components/Badge';
import { api } from '../services/api';
import { SAMPLE_DATASETS } from '../services/sampleData';
import { formatUploadDate, formatFileSize, computeDocumentStats } from '../utils/documentUtils';

export default function DocumentUpload({ onNavigate, onAnalyzeText, onIndexSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [indexResult, setIndexResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(null);

  // Uploaded and indexed documents state
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [docsError, setDocsError] = useState(null);
  const [totalChunksCount, setTotalChunksCount] = useState(0);
  const [showAllDocs, setShowAllDocs] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const fetchUploadedDocuments = useCallback(async () => {
    try {
      setLoadingDocs(true);
      setDocsError(null);
      const res = await api.getDocuments();
      const stats = computeDocumentStats(res);
      setUploadedDocs(stats.documents);
      setTotalChunksCount(stats.totalChunks);
    } catch (err) {
      setDocsError(err.message || 'Failed to retrieve uploaded documents list');
    } finally {
      setLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    fetchUploadedDocuments();
  }, [fetchUploadedDocuments]);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const dropped = e.dataTransfer?.files?.[0];
    if (dropped) {
      setFile(dropped);
      setUploadResult(null);
      setIndexResult(null);
      setError(null);
      setSelectedPreset(null);
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setUploadResult(null);
      setIndexResult(null);
      setError(null);
      setSelectedPreset(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      setUploading(true);
      setError(null);
      setUploadResult(null);
      setIndexResult(null);

      const res = await api.uploadDocument(file);
      setUploadResult(res);
    } catch (err) {
      setError(err.message || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleIndexRAG = async () => {
    if (!file) return;
    try {
      setIndexing(true);
      setError(null);
      const res = await api.indexDocument(file);
      setIndexResult(res);
      if (typeof onIndexSuccess === 'function') {
        onIndexSuccess();
      }
      // Reload the uploaded documents list to include the newly indexed document
      await fetchUploadedDocuments();
    } catch (err) {
      setError(err.message || 'Failed to index document in vector store');
    } finally {
      setIndexing(false);
    }
  };

  const handleSelectPreset = (preset) => {
    setSelectedPreset(preset);
    // Create a virtual text file from preset content
    const blob = new Blob([preset.text], { type: 'text/plain' });
    const virtualFile = new File([blob], preset.filename, { type: 'text/plain' });
    setFile(virtualFile);
    setUploadResult(null);
    setIndexResult(null);
    setError(null);
  };

  const handleCopyText = () => {
    const textToCopy = uploadResult?.extracted_text || selectedPreset?.text;
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const activeText = uploadResult?.extracted_text || selectedPreset?.text;
  const docFilename = indexResult?.document?.filename || indexResult?.filename || file?.name || 'document';
  const displayedDocs = showAllDocs ? uploadedDocs : uploadedDocs.slice(0, 3);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Upload className="w-6 h-6 text-blue-600" />
          Multi-Format Document Ingestion
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload project documents in <strong>PDF, DOCX, CSV, or TXT</strong> format. The FastAPI backend extracts text, analyzes metadata, and generates clean parsed representations for RAG indexing and autonomous agent analysis.
        </p>
      </div>

      {/* Responsive Two-Column Ingestion Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 lg:items-start">
        {/* Left Column (~65% on Desktop): Presets, Dropzone, Actions, Preview */}
        <div className="lg:col-span-2 flex flex-col gap-4 min-h-0">
          {/* Preset Selector */}
          <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs shrink-0">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              Load Realistic Enterprise Sample Document
            </h3>
            <p className="text-xs text-slate-500 mb-2.5">
              Select a sample document below to simulate realistic enterprise project files:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-2.5">
              {SAMPLE_DATASETS.map((p) => {
                const isSelected = selectedPreset?.id === p.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => handleSelectPreset(p)}
                    className={`p-2.5 rounded-lg border text-left transition-all cursor-pointer ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/70 shadow-xs'
                        : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                        p.type === 'pdf' ? 'bg-red-100 text-red-700' :
                        p.type === 'docx' ? 'bg-blue-100 text-blue-700' :
                        p.type === 'csv' ? 'bg-emerald-100 text-emerald-700' :
                        'bg-slate-200 text-slate-700'
                      }`}>
                        {p.type}
                      </span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-indigo-600" />}
                    </div>
                    <div className="font-semibold text-xs text-slate-900 truncate">{p.title}</div>
                    <div className="text-[11px] text-slate-500 truncate mt-0.5">{p.filename}</div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Dropzone & Action Box */}
          <div 
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`rounded-xl border-2 border-dashed transition-all p-4 sm:p-5 text-center flex flex-col items-center justify-center min-h-[170px] ${
              isDragging 
                ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20' 
                : 'border-slate-300 hover:border-blue-500 bg-white'
            }`}
          >
            <div className="w-9 h-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-2 shrink-0">
              <FolderOpen className="w-4 h-4" />
            </div>
            <h3 className="font-semibold text-slate-800 text-xs sm:text-sm">
              {file ? file.name : 'Choose a file or select a preset above'}
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5 max-w-sm">
              Supported file formats: <code className="text-blue-600 font-semibold">.pdf, .docx, .csv, .txt</code>
            </p>
            {file && (
              <div className="mt-1.5 text-[11px] text-slate-600 font-mono bg-slate-100 px-2.5 py-0.5 rounded-full shrink-0">
                {(file.size / 1024).toFixed(1)} KB • {file.type || 'text/plain'}
              </div>
            )}

            <div className="mt-3.5 flex flex-wrap items-center justify-center gap-2 shrink-0">
              <label className="cursor-pointer px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition border border-slate-300">
                Browse Files
                <input
                  type="file"
                  accept=".pdf,.docx,.csv,.txt"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>

              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer"
              >
                {uploading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Parsing Document...
                  </>
                ) : (
                  <>
                    <Upload className="w-3.5 h-3.5" />
                    Extract Document Metadata
                  </>
                )}
              </button>

              <button
                onClick={handleIndexRAG}
                disabled={!file || indexing}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer"
              >
                {indexing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Indexing into ChromaDB...
                  </>
                ) : (
                  <>
                    <Database className="w-3.5 h-3.5" />
                    Direct Index into RAG
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Feedback Alerts */}
          {error && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start gap-2.5 shrink-0">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Operation Failed</p>
                <p className="mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {indexResult && (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-start justify-between gap-2.5 shrink-0">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold">Successfully Indexed into ChromaDB</p>
                  <p className="mt-0.5">
                    Indexed <strong>{indexResult.chunks_created}</strong> semantic chunks from <em>{docFilename}</em>.
                    {indexResult.total_chunks !== undefined && (
                      <span className="ml-1 text-emerald-700">Total knowledge base chunks: <strong>{indexResult.total_chunks}</strong>.</span>
                    )}
                  </p>
                </div>
              </div>
              <button
                onClick={() => onNavigate('rag')}
                className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold whitespace-nowrap cursor-pointer"
              >
                Open RAG Search
              </button>
            </div>
          )}

          {/* Extracted Text Preview */}
          {activeText && (
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs shrink-0">
              <div className="flex items-center justify-between mb-2.5">
                <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  Extracted Document Text Preview
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopyText}
                    className="text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1 font-medium px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 transition cursor-pointer"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copied' : 'Copy Text'}
                  </button>
                  <button
                    onClick={() => onAnalyzeText(activeText)}
                    className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-1 font-medium px-3 py-1 rounded transition cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Analyze with Multi-Agent
                  </button>
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 font-mono text-xs text-slate-800 max-h-72 overflow-y-auto whitespace-pre-wrap leading-relaxed select-text">
                {activeText}
              </div>
            </div>
          )}
        </div>

        {/* Right Column (~35% on Desktop): Metadata, Specifications, Uploaded Documents */}
        <div className="flex flex-col gap-4 min-h-0">
          {/* Parsed Document Metadata */}
          <div className="bg-white rounded-xl border border-slate-200 p-3.5 sm:p-4 shadow-xs shrink-0">
            <h3 className="text-xs font-bold text-slate-800 mb-2 flex items-center gap-1.5 uppercase tracking-wider">
              <FileCheck className="w-3.5 h-3.5 text-emerald-600" />
              Parsed Document Metadata
            </h3>
            {uploadResult ? (
              <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs pt-0.5">
                <div className="col-span-2 flex items-center justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500 text-[11px]">Filename</span>
                  <span className="font-semibold text-slate-800 truncate max-w-[180px]" title={uploadResult.filename}>
                    {uploadResult.filename}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500 text-[11px]">Format</span>
                  <Badge variant="info" size="xs">.{uploadResult.file_type}</Badge>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500 text-[11px]">Document ID</span>
                  <span className="font-mono text-slate-700 text-[10px] truncate max-w-[80px]" title={uploadResult.document_id}>
                    {uploadResult.document_id}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500 text-[11px]">Characters</span>
                  <span className="font-mono font-bold text-slate-800 text-[11px]">
                    {uploadResult.character_count?.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500 text-[11px]">Words</span>
                  <span className="font-mono font-bold text-slate-800 text-[11px]">
                    {uploadResult.word_count?.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-500 text-[11px]">Lines</span>
                  <span className="font-mono font-bold text-slate-800 text-[11px]">
                    {uploadResult.line_count?.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-500 text-[11px]">Ingested At</span>
                  <span className="text-slate-600 text-[10px]">
                    {new Date(uploadResult.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ) : (
              <div className="py-2.5 px-3 text-center text-slate-400 text-xs italic bg-slate-50/70 rounded-lg border border-dashed border-slate-200">
                Upload a file to inspect its parsed metadata.
              </div>
            )}
          </div>

          {/* Highlighted Supported Formats Specification */}
          <div className="bg-gradient-to-br from-blue-50/70 to-indigo-50/40 rounded-xl border border-blue-200/90 p-3.5 shadow-xs shrink-0 space-y-2.5">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-blue-900 tracking-tight flex items-center gap-1.5 uppercase">
                <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                Supported Formats Specification
              </h4>
              <span className="text-[10px] text-blue-600 font-semibold bg-blue-100/70 px-2 py-0.5 rounded-full border border-blue-200">
                4 Formats
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {/* PDF */}
              <div className="bg-white p-2 rounded-lg border border-blue-100 shadow-2xs flex items-center justify-between gap-1.5">
                <div className="min-w-0">
                  <span className="font-bold text-xs text-slate-800 block">PDF</span>
                  <span className="text-[10px] text-slate-500 font-mono block truncate">PyMuPDF</span>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-100 text-rose-700 border border-rose-200 shrink-0">
                  .pdf
                </span>
              </div>

              {/* DOCX */}
              <div className="bg-white p-2 rounded-lg border border-blue-100 shadow-2xs flex items-center justify-between gap-1.5">
                <div className="min-w-0">
                  <span className="font-bold text-xs text-slate-800 block">DOCX</span>
                  <span className="text-[10px] text-slate-500 font-mono block truncate">python-docx</span>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-100 text-blue-700 border border-blue-200 shrink-0">
                  .docx
                </span>
              </div>

              {/* CSV */}
              <div className="bg-white p-2 rounded-lg border border-blue-100 shadow-2xs flex items-center justify-between gap-1.5">
                <div className="min-w-0">
                  <span className="font-bold text-xs text-slate-800 block">CSV</span>
                  <span className="text-[10px] text-slate-500 font-mono block truncate">Tabular records</span>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-700 border border-emerald-200 shrink-0">
                  .csv
                </span>
              </div>

              {/* TXT */}
              <div className="bg-white p-2 rounded-lg border border-blue-100 shadow-2xs flex items-center justify-between gap-1.5">
                <div className="min-w-0">
                  <span className="font-bold text-xs text-slate-800 block">TXT</span>
                  <span className="text-[10px] text-slate-500 font-mono block truncate">Direct UTF-8</span>
                </div>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-800 border border-amber-200 shrink-0">
                  .txt
                </span>
              </div>
            </div>
          </div>

          {/* Uploaded Documents Panel */}
          <div className="bg-white rounded-xl border border-slate-200 p-3.5 sm:p-4 shadow-xs flex flex-col min-h-0 space-y-3">
            {/* Header */}
            <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2.5 shrink-0">
              <div className="min-w-0">
                <h3 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-1.5 truncate">
                  <Database className="w-4 h-4 text-indigo-600 shrink-0" />
                  Uploaded Documents
                </h3>
                <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                  <Badge variant="primary" size="xs">
                    {uploadedDocs.length} {uploadedDocs.length === 1 ? 'Document' : 'Documents'}
                  </Badge>
                  <Badge variant="secondary" size="xs">
                    {totalChunksCount} {totalChunksCount === 1 ? 'Indexed Chunk' : 'Indexed Chunks'}
                  </Badge>
                </div>
              </div>

              <button
                onClick={fetchUploadedDocuments}
                disabled={loadingDocs}
                className="flex items-center gap-1 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border border-slate-300 px-2.5 py-1.5 rounded-lg transition disabled:opacity-50 cursor-pointer shadow-2xs shrink-0"
                title="Refresh uploaded documents list"
              >
                <RefreshCw className={`w-3.5 h-3.5 text-slate-600 ${loadingDocs ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>

            {/* Error Banner */}
            {docsError && (
              <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-xs flex items-center justify-between gap-2 shrink-0">
                <span className="flex items-center gap-1.5 truncate">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span className="truncate">{docsError}</span>
                </span>
                <button
                  onClick={fetchUploadedDocuments}
                  className="text-amber-800 underline font-semibold text-xs hover:text-amber-900 shrink-0 cursor-pointer"
                >
                  Retry
                </button>
              </div>
            )}

            {/* Vertically Scrollable Document List */}
            <div className="min-h-0 max-h-[420px] overflow-y-auto space-y-2 pr-1 divide-y divide-slate-100">
              {loadingDocs && uploadedDocs.length === 0 ? (
                <div className="py-8 text-center text-slate-400 text-xs">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto text-indigo-500 mb-2" />
                  Loading indexed documents...
                </div>
              ) : uploadedDocs.length === 0 ? (
                <div className="py-8 text-center">
                  <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-400 mx-auto flex items-center justify-center mb-1.5">
                    <FolderOpen className="w-4 h-4" />
                  </div>
                  <div className="text-xs font-semibold text-slate-700">No Documents Uploaded Yet</div>
                  <p className="text-[11px] text-slate-400 max-w-xs mx-auto mt-0.5">
                    Upload and index files above to see them cataloged here.
                  </p>
                </div>
              ) : (
                displayedDocs.map((doc, idx) => {
                  const fmt = (doc.file_type || '').toLowerCase();
                  const fmtVariant = ['pdf', 'docx', 'csv', 'txt'].includes(fmt) ? fmt : 'default';
                  const formattedDate = formatUploadDate(doc.uploaded_at);
                  const formattedSize = formatFileSize(doc.file_size_bytes);

                  return (
                    <div
                      key={doc.document_id || idx}
                      className="pt-2.5 first:pt-0 p-2.5 rounded-lg border border-slate-100 hover:border-slate-300 hover:bg-slate-50/70 transition-all space-y-2 bg-white"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2 min-w-0">
                          <FileText className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                          <div className="min-w-0">
                            <div className="font-semibold text-xs text-slate-800 truncate" title={doc.filename}>
                              {doc.filename}
                            </div>
                            <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-0.5 font-mono flex-wrap">
                              {formattedSize && <span>{formattedSize}</span>}
                              {formattedSize && formattedDate && <span>•</span>}
                              {formattedDate && <span>{formattedDate}</span>}
                            </div>
                          </div>
                        </div>
                        <Badge variant={fmtVariant} size="xs">
                          {fmt ? `.${fmt}` : 'FILE'}
                        </Badge>
                      </div>

                      <div className="flex items-center justify-between text-xs pt-1.5 border-t border-slate-100">
                        <span className="inline-flex items-center gap-1 font-mono font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md text-[11px]">
                          {doc.chunk_count}
                          <span className="font-sans font-normal text-[10px] text-slate-500">
                            {doc.chunk_count === 1 ? 'chunk' : 'chunks'}
                          </span>
                        </span>

                        <Badge variant="Completed" size="xs">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600 inline mr-1" />
                          {doc.status || 'Indexed'}
                        </Badge>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* View All / Show More Toggle */}
            {uploadedDocs.length > 3 && (
              <button
                type="button"
                onClick={() => setShowAllDocs((prev) => !prev)}
                className="w-full py-1.5 px-3 text-center text-xs font-semibold text-indigo-600 hover:text-indigo-800 bg-indigo-50/70 hover:bg-indigo-100/70 border border-indigo-200/60 rounded-lg transition cursor-pointer flex items-center justify-center gap-1.5 shrink-0 shadow-2xs"
              >
                {showAllDocs ? (
                  <>Show Less (Top 3)</>
                ) : (
                  <>View All ({uploadedDocs.length} Documents) • +{uploadedDocs.length - 3} more</>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
