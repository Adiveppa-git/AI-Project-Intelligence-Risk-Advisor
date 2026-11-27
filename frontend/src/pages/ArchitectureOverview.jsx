import React, { useState } from 'react';
import { 
  Layers, 
  Database, 
  Bot, 
  FileText, 
  ArrowRight, 
  Workflow, 
  Cpu, 
  Server, 
  CheckCircle2, 
  Code,
  ShieldCheck,
  ExternalLink
} from 'lucide-react';
import Badge from '../components/Badge';

export default function ArchitectureOverview() {
  const [activeSection, setActiveSection] = useState('pipeline');

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Workflow className="w-6 h-6 text-indigo-600" />
          Technical Architecture & System Design
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          High-level and low-level technical design of the <strong>AI-Driven Enterprise Project Intelligence & Risk Management Platform</strong>. Documents ingestion mechanisms, dense vector representations, agent decomposition, and data models.
        </p>
      </div>

      {/* Navigation Pills */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        <button
          onClick={() => setActiveSection('pipeline')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeSection === 'pipeline'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          1. End-to-End Pipeline
        </button>
        <button
          onClick={() => setActiveSection('ingestion')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeSection === 'ingestion'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          2. Document Ingestion & RAG
        </button>
        <button
          onClick={() => setActiveSection('agents')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeSection === 'agents'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          3. Multi-Agent Orchestration
        </button>
        <button
          onClick={() => setActiveSection('models')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition ${
            activeSection === 'models'
              ? 'bg-indigo-600 text-white shadow-xs'
              : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          4. Data Models & API Schemas
        </button>
      </div>

      {/* Section 1: End-to-End Pipeline */}
      {activeSection === 'pipeline' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-600" />
              Unified Architectural Blueprint
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              The platform connects enterprise document sources to autonomous reasoning agents via a low-latency RAG vector store and a FastAPI microservice backend:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
              <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/40 text-xs space-y-2">
                <span className="w-6 h-6 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-xs">1</span>
                <h4 className="font-bold text-blue-900">Document Ingestion</h4>
                <p className="text-slate-600 leading-relaxed text-[11px]">
                  PDF (pypdf), DOCX (python-docx), CSV (csv reader), TXT. Cleans text and counts words/chars/lines.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 text-xs space-y-2">
                <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center text-xs">2</span>
                <h4 className="font-bold text-indigo-900">Dense Embedding & RAG</h4>
                <p className="text-slate-600 leading-relaxed text-[11px]">
                  Chunked at 500 chars (50 overlap). Encoded with <code>all-MiniLM-L6-v2</code> into ChromaDB vector index.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-purple-200 bg-purple-50/40 text-xs space-y-2">
                <span className="w-6 h-6 rounded-full bg-purple-600 text-white font-bold flex items-center justify-center text-xs">3</span>
                <h4 className="font-bold text-purple-900">Parallel Agent Analysis</h4>
                <p className="text-slate-600 leading-relaxed text-[11px]">
                  Scope Agent, Risk Agent, and Blocker Agent execute concurrently using ThreadPoolExecutor with fallbacks.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50/40 text-xs space-y-2">
                <span className="w-6 h-6 rounded-full bg-emerald-600 text-white font-bold flex items-center justify-center text-xs">4</span>
                <h4 className="font-bold text-emerald-900">Synthesis & Dashboard</h4>
                <p className="text-slate-600 leading-relaxed text-[11px]">
                  Health scoring (0-100), executive summary, prioritized recommendations, and interactive React UI.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section 2: Ingestion & RAG */}
      {activeSection === 'ingestion' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-600" />
              Document Processing & Vector Search Details
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <h4 className="font-bold text-slate-800">Chunking & Token Strategy</h4>
                <p className="text-slate-600 leading-relaxed text-[11px]">
                  Documents are split into sliding chunks of <strong>500 characters</strong> with a <strong>50 character overlap</strong>. This preserves boundary context across sentences and deliverables without diluting semantic meaning.
                </p>
                <div className="font-mono text-[10px] bg-slate-200/70 p-2 rounded text-slate-700">
                  Chunk[i] = text[start : start + 500]<br />
                  start = i * (500 - 50)
                </div>
              </div>

              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <h4 className="font-bold text-slate-800">Vector Embeddings (all-MiniLM-L6-v2)</h4>
                <p className="text-slate-600 leading-relaxed text-[11px]">
                  384-dimensional dense vectors produced by HuggingFace SentenceTransformers. Cosine similarity queries rank chunks against agent queries to retrieve the highest relevance excerpts.
                </p>
                <div className="font-mono text-[10px] bg-slate-200/70 p-2 rounded text-slate-700">
                  cosine_sim(u, v) = (u • v) / (||u|| * ||v||)<br />
                  Chroma distance = 1 - cosine_similarity
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section 3: Agents */}
      {activeSection === 'agents' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Bot className="w-4 h-4 text-purple-600" />
              Multi-Agent Orchestrator Architecture
            </h3>

            <div className="space-y-3 text-xs">
              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
                <div className="flex items-center justify-between font-bold text-slate-800">
                  <span>1. Scope & Deliverable Extraction Agent</span>
                  <Badge variant="info" size="xs">Deterministic Parsing</Badge>
                </div>
                <p className="text-slate-600 text-[11px]">
                  Extracts project title, goals, in/out scope items, and authoritative deliverables. Cross-references team responsibility clauses to correlate owners to their exact original deliverable names.
                </p>
              </div>

              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
                <div className="flex items-center justify-between font-bold text-slate-800">
                  <span>2. Risk Detection & Delivery Forecasting Agent</span>
                  <Badge variant="medium" size="xs">5-Category Classifier</Badge>
                </div>
                <p className="text-slate-600 text-[11px]">
                  Classifies individual risks into Schedule, Budget, Dependency, Resource, or Delivery categories. Computes delivery forecasts and identifies potential resource bottlenecks.
                </p>
              </div>

              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
                <div className="flex items-center justify-between font-bold text-slate-800">
                  <span>3. Blocker & Action Item Agent</span>
                  <Badge variant="high" size="xs">Owner & Decision Tracker</Badge>
                </div>
                <p className="text-slate-600 text-[11px]">
                  Extracts active blockers with severity and impact, pending decisions with designated decision-makers, unresolved questions, delayed activities, and unassigned action item alerts.
                </p>
              </div>

              <div className="p-4 rounded-lg border border-purple-200 bg-purple-50/50 space-y-1.5">
                <div className="flex items-center justify-between font-bold text-purple-900">
                  <span>4. Multi-Agent Orchestrator & Health Calculator</span>
                  <Badge variant="low" size="xs">ThreadPoolExecutor</Badge>
                </div>
                <p className="text-slate-700 text-[11px]">
                  Dispatches requests across the agents simultaneously. If an individual agent throws an exception, the orchestrator catches it, populates fallback structures, marks <code>has_partial_failures = True</code>, and calculates the overall health score.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section 4: Data Models */}
      {activeSection === 'models' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Code className="w-4 h-4 text-emerald-600" />
              Pydantic Schemas & REST API Endpoints
            </h3>

            <div className="overflow-x-auto text-xs">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 font-semibold uppercase text-[10px]">
                    <th className="py-2 px-3">Method</th>
                    <th className="py-2 px-3">Endpoint Route</th>
                    <th className="py-2 px-3">Request Schema</th>
                    <th className="py-2 px-3">Response Schema</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                  <tr>
                    <td className="py-2 px-3 text-emerald-600 font-bold">GET</td>
                    <td className="py-2 px-3">/health</td>
                    <td className="py-2 px-3 text-slate-400">-</td>
                    <td className="py-2 px-3 text-slate-700">HealthResponse</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-blue-600 font-bold">POST</td>
                    <td className="py-2 px-3">/api/documents/upload</td>
                    <td className="py-2 px-3 text-slate-700">FormData (file)</td>
                    <td className="py-2 px-3 text-slate-700">DocumentUploadResponse</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-blue-600 font-bold">POST</td>
                    <td className="py-2 px-3">/api/rag/index</td>
                    <td className="py-2 px-3 text-slate-700">FormData (file)</td>
                    <td className="py-2 px-3 text-slate-700">RAGIndexResponse</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-blue-600 font-bold">POST</td>
                    <td className="py-2 px-3">/api/rag/search</td>
                    <td className="py-2 px-3 text-slate-700">RAGSearchRequest</td>
                    <td className="py-2 px-3 text-slate-700">RAGSearchResponse</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-blue-600 font-bold">POST</td>
                    <td className="py-2 px-3">/api/agents/analyze-scope</td>
                    <td className="py-2 px-3 text-slate-700">AgentAnalysisRequest</td>
                    <td className="py-2 px-3 text-slate-700">ScopeExtractionResponse</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-blue-600 font-bold">POST</td>
                    <td className="py-2 px-3">/api/agents/detect-risks</td>
                    <td className="py-2 px-3 text-slate-700">AgentAnalysisRequest</td>
                    <td className="py-2 px-3 text-slate-700">RiskAnalysisResponse</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-blue-600 font-bold">POST</td>
                    <td className="py-2 px-3">/api/agents/identify-blockers</td>
                    <td className="py-2 px-3 text-slate-700">AgentAnalysisRequest</td>
                    <td className="py-2 px-3 text-slate-700">BlockerAnalysisResponse</td>
                  </tr>
                  <tr>
                    <td className="py-2 px-3 text-blue-600 font-bold">POST</td>
                    <td className="py-2 px-3">/api/agents/analyze-project</td>
                    <td className="py-2 px-3 text-slate-700">MultiAgentAnalysisRequest</td>
                    <td className="py-2 px-3 text-slate-700">MultiAgentAnalysisResponse</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
