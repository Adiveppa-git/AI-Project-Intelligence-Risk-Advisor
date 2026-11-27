import React, { useState } from 'react';
import { 
  Upload, 
  FileText, 
  FileCode, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  Sparkles, 
  Copy, 
  Check, 
  Database, 
  Layers,
  FileCheck,
  RefreshCw,
  FolderOpen
} from 'lucide-react';
import Badge from '../components/Badge';
import { api } from '../services/api';
import { SAMPLE_DATASETS } from '../services/sampleData';

export default function DocumentUpload({ onNavigate, onAnalyzeText, onIndexSuccess }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [indexResult, setIndexResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(null);

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

      {/* Preset Selector */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
        <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          Load Realistic Enterprise Sample Document
        </h3>
        <p className="text-xs text-slate-500 mb-3">
          Select a sample document below to simulate realistic enterprise project files:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {SAMPLE_DATASETS.map((p) => {
            const isSelected = selectedPreset?.id === p.id;
            return (
              <button
                key={p.id}
                onClick={() => handleSelectPreset(p)}
                className={`p-3 rounded-lg border text-left transition-all ${
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-xl border-2 border-dashed border-slate-300 hover:border-blue-500 transition-colors p-8 text-center flex flex-col items-center justify-center">
            <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
              <FolderOpen className="w-7 h-7" />
            </div>
            <h3 className="font-semibold text-slate-800 text-base">
              {file ? file.name : 'Choose a file or select a preset above'}
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              Supported file formats: <code className="text-blue-600 font-semibold">.pdf, .docx, .csv, .txt</code>
            </p>
            {file && (
              <div className="mt-2 text-xs text-slate-600 font-mono bg-slate-100 px-3 py-1 rounded-full">
                {(file.size / 1024).toFixed(1)} KB • {file.type || 'text/plain'}
              </div>
            )}

            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <label className="cursor-pointer px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition border border-slate-300">
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
                className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer"
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
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition shadow-xs flex items-center gap-1.5 cursor-pointer"
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
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Operation Failed</p>
                <p className="mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {indexResult && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-start justify-between gap-2.5">
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
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
              <div className="flex items-center justify-between mb-3">
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

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 font-mono text-xs text-slate-800 max-h-80 overflow-y-auto whitespace-pre-wrap leading-relaxed select-text">
                {activeText}
              </div>
            </div>
          )}
        </div>

        {/* Right Col: Metadata and Quick Pipeline Dispatch */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-emerald-600" />
              Parsed Document Metadata
            </h3>
            {uploadResult ? (
              <div className="space-y-2.5 text-xs">
                <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Document ID</span>
                  <span className="font-mono text-slate-800 truncate max-w-[150px]">{uploadResult.document_id}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Filename</span>
                  <span className="font-medium text-slate-800 truncate max-w-[150px]">{uploadResult.filename}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Format</span>
                  <Badge variant="info" size="xs">.{uploadResult.file_type}</Badge>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Character Count</span>
                  <span className="font-mono font-bold text-slate-800">{uploadResult.character_count?.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Word Count</span>
                  <span className="font-mono font-bold text-slate-800">{uploadResult.word_count?.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between py-1.5 border-b border-slate-100">
                  <span className="text-slate-500">Line Count</span>
                  <span className="font-mono font-bold text-slate-800">{uploadResult.line_count?.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between py-1.5">
                  <span className="text-slate-500">Ingested At</span>
                  <span className="text-slate-600 text-[11px]">{new Date(uploadResult.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-slate-400 text-xs">
                Upload a file to inspect its parsed metadata.
              </div>
            )}
          </div>

          <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 text-xs space-y-2">
            <h4 className="font-bold text-slate-800">Supported Formats Specification</h4>
            <ul className="space-y-1.5 text-slate-600 text-[11px]">
              <li>• <strong>PDF:</strong> Extracted via <code className="font-mono bg-slate-200 px-1 rounded">pymupdf</code> page-by-page.</li>
              <li>• <strong>DOCX:</strong> Extracted via <code className="font-mono bg-slate-200 px-1 rounded">python-docx</code> paragraph & table parsing.</li>
              <li>• <strong>CSV:</strong> Parsed row-by-row into structured tabular records.</li>
              <li>• <strong>TXT:</strong> Direct UTF-8 sanitized ingestion.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
