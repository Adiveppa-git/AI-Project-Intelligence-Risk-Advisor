import React, { useState, useEffect } from 'react';
import { 
  Database, 
  Search, 
  Sparkles, 
  Layers, 
  FileText, 
  Upload, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Sliders, 
  Maximize2,
  Filter,
  Check
} from 'lucide-react';
import Badge from '../components/Badge';
import EvidenceModal from '../components/EvidenceModal';
import { api } from '../services/api';

const QUICK_QUERIES = [
  "What are the main objectives and deliverables of this project?",
  "telemetry pipeline delay and blockers",
  "budget overrun and licensing costs",
  "RBAC gateway milestone and developer constraints",
  "unassigned action items and decisions",
  "data warehouse integration sync owner"
];

const KNOWN_DOCUMENTS = [
  { id: 'ALL', label: 'All Indexed Documents' },
  { id: 'project_charter.pdf', label: 'project_charter.pdf' },
  { id: 'project_proposal.txt', label: 'project_proposal.txt' },
  { id: 'sample_project_report.txt', label: 'sample_project_report.txt' },
  { id: 'progress_report.docx', label: 'progress_report.docx' },
  { id: 'task_list.csv', label: 'task_list.csv' },
  { id: 'meeting_notes.txt', label: 'meeting_notes.txt' },
];

export default function RAGPipeline({ onIndexSuccess }) {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(3);
  const [selectedFilter, setSelectedFilter] = useState('ALL');
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [status, setStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [error, setError] = useState(null);
  const [selectedEvidence, setSelectedEvidence] = useState(null);

  // Ingestion state
  const [indexFile, setIndexFile] = useState(null);
  const [indexing, setIndexing] = useState(false);
  const [indexSuccess, setIndexSuccess] = useState(null);

  const fetchStatus = async () => {
    try {
      setLoadingStatus(true);
      const res = await api.getRAGStatus();
      setStatus(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleSearch = async (searchQuery = query, filter = selectedFilter) => {
    const q = searchQuery.trim();
    if (!q) return;
    try {
      setSearching(true);
      setError(null);
      const payload = {
        query: q,
        top_k: topK,
        ...(filter && filter !== 'ALL' ? { filename: filter } : {}),
      };
      const res = await api.searchRAG(payload);
      setResults(res);
    } catch (err) {
      setError(err.message || 'RAG search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleIndexFile = async () => {
    if (!indexFile) return;
    try {
      setIndexing(true);
      setError(null);
      setIndexSuccess(null);
      const res = await api.indexDocument(indexFile);
      const docName = res.document?.filename || res.filename || indexFile?.name || 'document';
      const totalCount = res.total_chunks || (status?.indexed_chunks ? status.indexed_chunks + res.chunks_created : res.chunks_created);
      setIndexSuccess(`Successfully indexed ${res.chunks_created} chunks from "${docName}"! Total knowledge base chunks: ${totalCount}.`);
      setIndexFile(null);
      fetchStatus();
      if (typeof onIndexSuccess === 'function') {
        onIndexSuccess();
      }
    } catch (err) {
      setError(err.message || 'Failed to index file');
    } finally {
      setIndexing(false);
    }
  };

  const getSimilarityBadge = (score) => {
    const num = parseFloat(score);
    if (isNaN(num)) return { label: 'Relevance', variant: 'info' };
    if (num >= 0.50) return { label: `${(num * 100).toFixed(1)}% High Match`, variant: 'low' };
    if (num >= 0.35) return { label: `${(num * 100).toFixed(1)}% Relevant`, variant: 'info' };
    return { label: `${(num * 100).toFixed(1)}% Partial`, variant: 'medium' };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Database className="w-6 h-6 text-indigo-600" />
          RAG Knowledge Base & Vector Retrieval
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Semantic dense retrieval powered by <strong>ChromaDB</strong> and <strong>sentence-transformers (all-MiniLM-L6-v2)</strong>. Generates 384-dimensional dense vectors to match queries against project documentation via cosine similarity.
        </p>
      </div>

      {/* Vector Store Status & Indexing Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ChromaDB Status Card */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Database className="w-4 h-4 text-indigo-600" />
                ChromaDB Vector Store
              </h3>
              <button
                onClick={fetchStatus}
                className="text-slate-400 hover:text-slate-700 transition cursor-pointer"
                title="Refresh Status"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingStatus ? 'animate-spin text-indigo-600' : ''}`} />
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Collection Name</span>
                <span className="font-mono font-semibold text-slate-800">{status?.collection_name || 'project_chunks'}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Embedding Model</span>
                <span className="font-mono text-slate-800">{status?.embedding_model || 'all-MiniLM-L6-v2'}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Vector Dimensions</span>
                <span className="font-mono text-slate-800">384-dim dense float32</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Indexed Chunks</span>
                <span className="font-mono font-bold text-indigo-600 text-sm">
                  {status?.indexed_chunks ?? 0} chunks
                </span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-slate-500">Distance Metric</span>
                <span className="font-mono text-slate-700">Cosine Distance (HNSW)</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-400">Persistence Directory</span>
            <span className="font-mono text-[10px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded truncate max-w-[200px]" title={status?.storage_path || 'backend/data/chroma'}>
              {status?.storage_path ? status.storage_path.split('\\').slice(-3).join('/') : 'backend/data/chroma'}
            </span>
          </div>
        </div>

        {/* Ingestion & Chunking Box */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2 mb-2">
              <Upload className="w-4 h-4 text-blue-600" />
              Index New Document into Knowledge Base
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              Chunks document into boundary-aware segments with sliding overlap, encodes embeddings with <code>all-MiniLM-L6-v2</code>, and persists vectors into ChromaDB:
            </p>

            <div className="flex flex-wrap items-center gap-3">
              <input
                type="file"
                accept=".pdf,.docx,.csv,.txt"
                onChange={(e) => setIndexFile(e.target.files[0])}
                className="text-xs text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-100 file:text-slate-700 hover:file:bg-slate-200 cursor-pointer"
              />
              <button
                onClick={handleIndexFile}
                disabled={!indexFile || indexing}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-xs rounded-lg transition flex items-center gap-1.5 cursor-pointer"
              >
                {indexing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Chunking & Indexing...
                  </>
                ) : (
                  <>
                    <Database className="w-3.5 h-3.5" />
                    Index File Chunks
                  </>
                )}
              </button>
            </div>
          </div>

          {indexSuccess && (
            <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{indexSuccess}</span>
            </div>
          )}
        </div>
      </div>

      {/* Semantic Search Interface */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Search className="w-5 h-5 text-indigo-600" />
            Interactive Semantic Search
          </h2>
          <div className="flex flex-wrap items-center gap-4 text-xs">
            {/* Metadata Document Filter */}
            <div className="flex items-center gap-1.5 text-slate-600">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <span>Scope:</span>
              <select
                value={selectedFilter}
                onChange={(e) => {
                  setSelectedFilter(e.target.value);
                  if (query.trim()) handleSearch(query, e.target.value);
                }}
                className="bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 text-xs text-slate-700 font-medium focus:ring-1 focus:ring-indigo-500 cursor-pointer"
              >
                {KNOWN_DOCUMENTS.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Top K Chunks Slider */}
            <div className="flex items-center gap-1.5 text-slate-600">
              <Sliders className="w-3.5 h-3.5" />
              <span>Top K:</span>
              <span className="font-bold text-indigo-600 font-mono w-4">{topK}</span>
              <input
                type="range"
                min="1"
                max="10"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-20 accent-indigo-600 cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* Search Input Bar */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Ask a question about deliverables, schedule risks, owners, or blockers..."
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:bg-white transition"
            />
          </div>
          <button
            onClick={() => handleSearch()}
            disabled={searching || !query.trim()}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition shadow-xs flex items-center gap-2 whitespace-nowrap cursor-pointer"
          >
            {searching ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Retrieving...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Semantic Search
              </>
            )}
          </button>
        </div>

        {/* Suggested Queries */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs text-slate-400 font-medium">Try asking:</span>
          {QUICK_QUERIES.map((q, i) => (
            <button
              key={i}
              onClick={() => {
                setQuery(q);
                handleSearch(q);
              }}
              className="text-xs bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600 px-2.5 py-1 rounded-lg border border-slate-200 transition cursor-pointer"
            >
              {q}
            </button>
          ))}
        </div>

        {error && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Search Results Display */}
      {results && (
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">
                Retrieved Context Results ({results.results?.length || 0} chunks)
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Query: <span className="italic font-medium text-slate-700">"{results.query}"</span>
                {selectedFilter !== 'ALL' && (
                  <span className="ml-2 text-indigo-600 font-semibold">• Filtered by {selectedFilter}</span>
                )}
              </p>
            </div>
            <Badge variant="info" size="xs">MiniLM-L6-v2 Embeddings</Badge>
          </div>

          {results.results?.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              No matching chunks found for the current query and filter.
            </div>
          ) : (
            <div className="space-y-3">
              {results.results?.map((item, idx) => {
                const simValue = item.similarity !== undefined ? item.similarity : (1 - item.distance);
                const simBadge = getSimilarityBadge(simValue);
                const docName = item.filename || item.metadata?.filename || 'Document';
                const chunkNum = item.chunk_index !== undefined ? item.chunk_index + 1 : idx + 1;

                return (
                  <div
                    key={item.chunk_id || idx}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-indigo-300 transition-all space-y-2 group"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-2.5">
                        <span className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center text-[10px]">
                          #{idx + 1}
                        </span>
                        
                        {/* Filename & Chunk Index */}
                        <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                          <FileText className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
                          <span>{docName}</span>
                          <span className="font-mono text-slate-400 text-[11px] font-normal">
                            (Chunk #{chunkNum})
                          </span>
                        </div>

                        {/* Chunk ID Pill */}
                        <span 
                          className="font-mono text-[10px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded truncate max-w-[110px]"
                          title={`Chunk ID: ${item.chunk_id}`}
                        >
                          ID: {item.chunk_id ? `${item.chunk_id.slice(0, 8)}...` : `idx-${idx}`}
                        </span>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-500 text-[11px]">Similarity:</span>
                            <strong className="text-indigo-600 font-mono text-xs">{simValue.toFixed(4)}</strong>
                            <Badge variant={simBadge.variant} size="xs">{simBadge.label}</Badge>
                          </div>
                          {item.distance !== undefined && (
                            <span className="text-[10px] text-slate-400 font-mono block">
                              Cosine Distance: {item.distance.toFixed(4)}
                            </span>
                          )}
                        </div>

                        <button
                          onClick={() => setSelectedEvidence({
                            title: `${docName} (Chunk #${chunkNum})`,
                            evidence: item.text,
                            confidence: simValue.toFixed(4),
                            source: `${docName} • Chunk ID: ${item.chunk_id || 'ChromaDB'}`
                          })}
                          className="text-slate-500 hover:text-indigo-600 flex items-center gap-1 font-medium text-xs px-2.5 py-1 rounded bg-white border border-slate-200 shadow-2xs hover:border-indigo-300 transition cursor-pointer"
                        >
                          <Maximize2 className="w-3.5 h-3.5" />
                          Inspect Chunk
                        </button>
                      </div>
                    </div>

                    <p className="text-xs text-slate-700 font-sans leading-relaxed whitespace-pre-wrap select-text pl-7">
                      {item.text}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Evidence Modal */}
      <EvidenceModal
        isOpen={!!selectedEvidence}
        onClose={() => setSelectedEvidence(null)}
        title={selectedEvidence?.title}
        evidence={selectedEvidence?.evidence}
        confidence={selectedEvidence?.confidence}
        source={selectedEvidence?.source}
      />
    </div>
  );
}
