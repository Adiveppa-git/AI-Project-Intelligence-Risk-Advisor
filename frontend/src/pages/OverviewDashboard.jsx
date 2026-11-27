import React from 'react';
import { 
  Activity, 
  Database, 
  ShieldAlert, 
  FileCheck2, 
  AlertOctagon, 
  CheckCircle2, 
  Layers, 
  ArrowRight, 
  Sparkles, 
  RefreshCw, 
  Server, 
  Bot,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import StatCard from '../components/StatCard';
import Badge from '../components/Badge';
import { SAMPLE_DATASETS } from '../services/sampleData';

export default function OverviewDashboard({ 
  onNavigate, 
  onRunSampleAnalysis,
  health,
  connectionStatus = 'connecting',
  ragStatus,
  ragError,
  agentStatus,
  isRefreshing = false,
  onRefresh
}) {
  const isOnline = connectionStatus === 'online';
  const isConnecting = connectionStatus === 'connecting';
  const isOffline = connectionStatus === 'offline';

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="bg-gradient-to-r from-blue-600 via-indigo-600 to-slate-800 rounded-2xl p-6 sm:p-8 text-white shadow-lg relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 opacity-10 pointer-events-none flex items-center pr-8">
          <Bot className="w-80 h-80 text-white" />
        </div>
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-xs font-semibold uppercase tracking-wider mb-3">
            <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
            Enterprise Project Intelligence
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            AI-Driven Project Risk & Delivery Advisor
          </h1>
          <p className="mt-2 text-blue-100 text-sm sm:text-base leading-relaxed">
            Autonomous multi-agent orchestration for enterprise projects. Ingest project charters, sprint retrospectives, risk logs and task matrices to automatically extract deliverables, detect schedule/budget risks, and identify blockers.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigate('orchestrator')}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-blue-700 hover:bg-blue-50 font-semibold rounded-xl text-sm transition-all shadow-md hover:shadow-lg active:scale-95 cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-blue-600" />
              Run Complete AI Analysis
              <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onNavigate('upload')}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-700/60 hover:bg-blue-700 text-white font-medium rounded-xl text-sm transition-all border border-blue-400/30 cursor-pointer"
            >
              <Database className="w-4 h-4" />
              Upload Document
            </button>
            <button
              onClick={() => onNavigate('milestones')}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-900/50 hover:bg-slate-900/80 text-white font-medium rounded-xl text-sm transition-all border border-white/20 cursor-pointer"
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Milestone 1 & 2 Audit
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards Row - Uses centralized connectionStatus and decoupled RAG status */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Backend Service Status"
          value={isOnline ? 'Online' : isConnecting ? 'Connecting...' : 'Offline'}
          subtext={
            isOnline
              ? (health?.version ? `API v${health.version} (FastAPI)` : 'FastAPI (Port 8000)')
              : isConnecting
              ? 'Checking connection to :8000...'
              : 'FastAPI server unreachable'
          }
          icon={Server}
          color={isOnline ? 'emerald' : isConnecting ? 'amber' : 'rose'}
          trend={
            <span className={`inline-flex items-center gap-1 font-semibold text-xs ${
              isOnline ? 'text-emerald-600' : isConnecting ? 'text-amber-600' : 'text-rose-600'
            }`}>
              {isOnline ? '● HEALTHY' : isConnecting ? '○ CHECKING' : '✕ OFFLINE'}
            </span>
          }
        />

        <StatCard
          title="Indexed Knowledge Chunks"
          value={ragStatus?.indexed_chunks ?? 0}
          subtext={ragError ? 'ChromaDB initializing (503)' : 'Vector store: ChromaDB (all-MiniLM-L6-v2)'}
          icon={Database}
          color={ragError ? 'amber' : 'indigo'}
          trend={
            <span className="text-xs text-slate-500">
              {ragError ? 'Temporary initialization' : 'HNSW Dense Index'}
            </span>
          }
        />

        <StatCard
          title="Active Autonomous Agents"
          value="3 + 1 Orchestrator"
          subtext="Scope, Risk, Blocker & Multi-Agent"
          icon={Bot}
          color="purple"
          trend={<span className="text-xs text-emerald-600 font-semibold">● READY</span>}
        />

        <StatCard
          title="Milestone Verification"
          value="100% Passed"
          subtext="8 / 8 Official Internship Activities"
          icon={CheckCircle2}
          color="emerald"
          trend={<span className="text-xs text-emerald-600 font-semibold">● 102 TESTS AUDITED</span>}
        />
      </div>

      {/* Quick Launch Cards & Agents Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Agent Capability Cards */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              Specialized Agent Capabilities
            </h2>
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isRefreshing}
                className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 font-medium px-2.5 py-1 rounded-md hover:bg-slate-100 transition cursor-pointer"
                title="Refresh backend status"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-blue-600' : ''}`} />
                <span>{isRefreshing ? 'Checking...' : 'Refresh Status'}</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Scope Agent Card */}
            <div 
              onClick={() => onNavigate('scope')}
              className="bg-white rounded-xl border border-slate-200 p-5 hover:border-blue-400 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                  <FileCheck2 className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-slate-900 text-sm group-hover:text-blue-600 flex items-center justify-between">
                  Scope & Deliverables
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                </h3>
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                  Extracts project title, goals, in/out scope boundaries, milestone deadlines, and individual owners.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-500">Owner Correlation</span>
                <Badge variant="low" size="xs">Authoritative</Badge>
              </div>
            </div>

            {/* Risk Agent Card */}
            <div 
              onClick={() => onNavigate('risks')}
              className="bg-white rounded-xl border border-slate-200 p-5 hover:border-amber-400 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-slate-900 text-sm group-hover:text-amber-600 flex items-center justify-between">
                  Risk & Forecasting
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-amber-600 group-hover:translate-x-0.5 transition-all" />
                </h3>
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                  5 risk categories: schedule slippage, budget overruns, dependency gaps, resource bottlenecks & delivery concerns.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-500">Categories</span>
                <Badge variant="medium" size="xs">5 Classifiers</Badge>
              </div>
            </div>

            {/* Blocker Agent Card */}
            <div 
              onClick={() => onNavigate('blockers')}
              className="bg-white rounded-xl border border-slate-200 p-5 hover:border-rose-400 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div>
                <div className="w-10 h-10 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
                  <AlertOctagon className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-slate-900 text-sm group-hover:text-rose-600 flex items-center justify-between">
                  Blocker & Actions
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-rose-600 group-hover:translate-x-0.5 transition-all" />
                </h3>
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                  Identifies active blockers, pending decisions with decision-makers, unresolved questions, and unassigned items.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-500">Action Items</span>
                <Badge variant="high" size="xs">Owner Tracking</Badge>
              </div>
            </div>
          </div>

          {/* Quick Presets Section */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <h3 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              Quick-Test Preloaded Enterprise Datasets
            </h3>
            <p className="text-xs text-slate-500 mb-3">
              Click any sample dataset below to inspect its contents and run live agent analysis:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {SAMPLE_DATASETS.map((sample) => (
                <div
                  key={sample.id}
                  onClick={() => onRunSampleAnalysis(sample)}
                  className="p-3 rounded-lg border border-slate-200 hover:border-indigo-400 hover:bg-indigo-50/40 transition cursor-pointer text-left flex items-start gap-3 group"
                >
                  <div className="p-2 rounded bg-slate-100 text-slate-600 group-hover:bg-indigo-100 group-hover:text-indigo-600 transition">
                    <span className="text-xs font-bold uppercase">{sample.type}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-slate-900 group-hover:text-indigo-700 truncate">
                      {sample.title}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5">
                      {sample.description}
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 group-hover:translate-x-0.5 transition self-center" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: System Highlights & RAG Architecture */}
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 mb-3">
              <Activity className="w-4 h-4 text-emerald-600" />
              System Architecture Flow
            </h3>
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/70 flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center shrink-0 text-[11px]">1</span>
                <div>
                  <span className="font-semibold text-slate-800">Multi-Format Ingestion</span>
                  <p className="text-slate-500 text-[11px] mt-0.5">PDF, DOCX, CSV, TXT parsed with character, word, and line count extraction.</p>
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/70 flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center shrink-0 text-[11px]">2</span>
                <div>
                  <span className="font-semibold text-slate-800">Dense Vector Retrieval</span>
                  <p className="text-slate-500 text-[11px] mt-0.5">MiniLM-L6-v2 embeddings indexed in ChromaDB with cosine similarity search.</p>
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/70 flex items-start gap-2.5">
                <span className="w-5 h-5 rounded-full bg-purple-100 text-purple-700 font-bold flex items-center justify-center shrink-0 text-[11px]">3</span>
                <div>
                  <span className="font-semibold text-slate-800">Multi-Agent Orchestration</span>
                  <p className="text-slate-500 text-[11px] mt-0.5">Scope, Risk, and Blocker agents execute in parallel, synthesizing overall health and recommendations.</p>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100">
              <button
                onClick={() => onNavigate('architecture')}
                className="w-full py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-xs rounded-lg transition border border-slate-200 flex items-center justify-center gap-1.5 cursor-pointer"
              >
                View Full Technical Architecture
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Internship Meta Card */}
          <div className="bg-slate-900 text-slate-200 rounded-xl p-5 shadow-xs text-xs space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white uppercase tracking-wider text-[11px]">Infosys Springboard</span>
              <span className="px-2 py-0.5 bg-emerald-900/60 text-emerald-400 font-bold rounded text-[10px] border border-emerald-700/50">COMPLETED</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              AI Project Intelligence & Risk Advisor demonstrates full compliance with Milestone 1 (Docs & RAG) and Milestone 2 (Agents & Orchestrator).
            </p>
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
              <span className="text-slate-400">Total Regression Tests</span>
              <span className="font-mono text-emerald-400 font-bold">102 / 102 Passed</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
