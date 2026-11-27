import React from 'react';
import {
  Activity,
  Layers,
  UploadCloud,
  Database,
  Target,
  AlertTriangle,
  ShieldAlert,
  Cpu,
  Milestone,
  CheckCircle2,
  XCircle,
  ExternalLink,
} from 'lucide-react';

export default function Header({
  activeTab,
  systemStatus,
  connectionStatus, // 'online' | 'connecting' | 'offline'
  ragStatus,
  ragError,
  onRunAnalysis,
  analyzing = false,
}) {
  const titles = {
    overview: {
      title: 'Executive Project Overview',
      subtitle: 'Real-time multi-agent intelligence and delivery risk advisor',
    },
    upload: {
      title: 'Document Ingestion Pipeline',
      subtitle: 'Upload and parse project charters, specs, notes, and task lists (PDF, DOCX, CSV, TXT)',
    },
    rag: {
      title: 'RAG Knowledge Base & Vector Retrieval',
      subtitle: 'Semantic search, ChromaDB vector indexing, and boundary-aware chunking',
    },
    scope: {
      title: 'Scope & Deliverable Extraction Agent',
      subtitle: 'Authoritative extraction of deliverables, milestones, boundaries, and team roles',
    },
    risks: {
      title: 'Risk Detection & Delivery Forecasting Agent',
      subtitle: 'Detection of schedule slips, budget constraints, technical bottlenecks, and delivery forecast',
    },
    blockers: {
      title: 'Blocker & Action Item Identification Agent',
      subtitle: 'Extraction of active impediments, pending architectural decisions, and owned actions',
    },
    orchestrator: {
      title: 'Multi-Agent Autonomous Orchestrator',
      subtitle: 'Unified enterprise analysis combining all three agents into an executive briefing',
    },
    milestones: {
      title: 'Internship Milestone Tracker',
      subtitle: 'Milestone 1 & Milestone 2 official activities, status, descriptions, and verification evidence',
    },
    architecture: {
      title: 'System Architecture & Technical Design',
      subtitle: 'RAG pipeline dataflow, multi-agent coordination pattern, and schema lineage',
    },
  };

  const current = titles[activeTab] || titles.overview;

  // Derive explicit connection state:
  // Priority: explicit connectionStatus prop ('online' | 'connecting' | 'offline')
  // Fallback: evaluate systemStatus from GET /health
  let effectiveStatus = connectionStatus;
  if (!effectiveStatus) {
    if (systemStatus?.status === 'ok' || systemStatus?.status === 'ready') {
      effectiveStatus = 'online';
    } else if (systemStatus === null) {
      effectiveStatus = 'offline';
    } else {
      effectiveStatus = 'connecting';
    }
  }

  const isOnline = effectiveStatus === 'online';
  const isConnecting = effectiveStatus === 'connecting';
  const isOffline = effectiveStatus === 'offline';

  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-8 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 className="text-xl font-bold text-slate-800 tracking-tight flex items-center gap-2">
          {current.title}
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">{current.subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        {/* Backend Connectivity Status Pill - depends directly on GET /health */}
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors ${
            isOnline
              ? 'bg-emerald-50/70 border-emerald-200 text-emerald-800'
              : isConnecting
              ? 'bg-amber-50/70 border-amber-200 text-amber-800'
              : 'bg-rose-50/70 border-rose-200 text-rose-800'
          }`}
          title={
            isOnline
              ? 'FastAPI backend is online and reachable at :8000'
              : isConnecting
              ? 'Checking connection to FastAPI backend...'
              : 'Cannot connect to FastAPI backend at :8000'
          }
        >
          <span className="relative flex h-2 w-2">
            {isOnline && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-emerald-400" />
            )}
            {isConnecting && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 bg-amber-400" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isOnline
                  ? 'bg-emerald-500'
                  : isConnecting
                  ? 'bg-amber-500'
                  : 'bg-rose-500'
              }`}
            />
          </span>
          <span>
            FastAPI:{' '}
            {isOnline ? 'Online (8000)' : isConnecting ? 'Connecting...' : 'Offline'}
          </span>
        </div>

        {/* Vector DB Stats Pill - handled independently so RAG status does not affect FastAPI status */}
        {ragStatus && ragStatus.indexed_chunks !== undefined ? (
          <div className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-indigo-50 border border-indigo-100 text-xs text-indigo-700 font-medium">
            <Database className="w-3.5 h-3.5" />
            <span>ChromaDB: {ragStatus.indexed_chunks ?? 0} Chunks</span>
          </div>
        ) : ragError ? (
          <div
            className="hidden lg:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-xs text-slate-500 font-medium"
            title={`ChromaDB initializing or temporarily unavailable (${ragError})`}
          >
            <Database className="w-3.5 h-3.5 text-slate-400" />
            <span>ChromaDB: Initializing</span>
          </div>
        ) : null}

        {/* Action Button: Run Complete Analysis */}
        {onRunAnalysis && (
          <button
            onClick={onRunAnalysis}
            disabled={analyzing}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-60 text-white rounded-xl text-xs font-semibold shadow-sm shadow-indigo-200 transition-all cursor-pointer"
          >
            <Cpu className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
            <span>{analyzing ? 'Analyzing Platform...' : 'Run Multi-Agent Analysis'}</span>
          </button>
        )}
      </div>
    </header>
  );
}
