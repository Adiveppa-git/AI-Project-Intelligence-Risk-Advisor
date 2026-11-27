import React, { useState } from 'react';
import { 
  FileCheck2, 
  Sparkles, 
  Users, 
  Calendar, 
  CheckCircle2, 
  XCircle, 
  ArrowRight, 
  AlertCircle, 
  RefreshCw, 
  Maximize2,
  Code
} from 'lucide-react';
import Badge from '../components/Badge';
import EvidenceModal from '../components/EvidenceModal';
import { api } from '../services/api';
import { SAMPLE_DATASETS } from '../services/sampleData';

export default function ScopeAgentPage({ preloadedText }) {
  const [inputText, setInputText] = useState(preloadedText || SAMPLE_DATASETS[0].text);
  const [selectedFilename, setSelectedFilename] = useState(SAMPLE_DATASETS[0].filename);
  const [analyzing, setAnalyzing] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [showRaw, setShowRaw] = useState(false);

  const handleAnalyze = async () => {
    if (!inputText.trim()) return;
    try {
      setAnalyzing(true);
      setError(null);
      const res = await api.analyzeScope({ text: inputText, filename: selectedFilename });
      setData(res);
    } catch (err) {
      setError(err.message || 'Scope analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <FileCheck2 className="w-6 h-6 text-blue-600" />
          Scope & Deliverable Extraction Agent
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Specialized agent that parses project titles, core objectives, in/out scope boundaries, milestones, and extracts authoritative deliverables while maintaining team ownership correlations.
        </p>
      </div>

      {/* Input Panel */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <label className="text-sm font-bold text-slate-800 flex items-center gap-2">
            Project Scope Input Document
          </label>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Presets:</span>
            {SAMPLE_DATASETS.slice(0, 2).map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setInputText(s.text);
                  setSelectedFilename(s.filename);
                }}
                className="text-xs bg-slate-100 hover:bg-blue-50 hover:text-blue-600 text-slate-600 px-2 py-1 rounded transition"
              >
                {s.title.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>

        <textarea
          rows={6}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste project charter, scope statement, or team responsibility breakdown..."
          className="w-full p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-blue-500 focus:bg-white leading-relaxed transition"
        />

        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {inputText.length} characters • {inputText.split(/\s+/).filter(Boolean).length} words
          </span>
          <button
            onClick={handleAnalyze}
            disabled={analyzing || !inputText.trim()}
            className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition shadow-xs flex items-center gap-2"
          >
            {analyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Extracting Scope...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Analyze Project Scope
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Extraction Results */}
      {data && (
        <div className="space-y-6">
          {/* Top Title & Objectives Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Project Title</span>
              <h2 className="text-lg font-bold text-slate-900 mt-1">
                {data.project_title || 'Untitled Project'}
              </h2>
            </div>
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Core Objectives</span>
              <div className="mt-1 space-y-1">
                {data.objectives?.length ? (
                  data.objectives.map((obj, i) => (
                    <p key={i} className="text-xs text-slate-700 leading-relaxed">• {obj}</p>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 italic">No specific objectives extracted.</p>
                )}
              </div>
            </div>
          </div>

          {/* In-Scope vs Out-of-Scope Columns */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-emerald-50/50 rounded-xl border border-emerald-200 p-5 shadow-xs">
              <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm mb-3">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                In-Scope Deliverables & Features ({data.in_scope?.length || 0})
              </div>
              <ul className="space-y-1.5 text-xs text-emerald-950">
                {data.in_scope?.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-emerald-500 font-bold">✓</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-50 rounded-xl border border-slate-200 p-5 shadow-xs">
              <div className="flex items-center gap-2 text-slate-700 font-bold text-sm mb-3">
                <XCircle className="w-4 h-4 text-slate-400" />
                Out-of-Scope Exclusions ({data.out_of_scope?.length || 0})
              </div>
              <ul className="space-y-1.5 text-xs text-slate-600">
                {data.out_of_scope?.length ? (
                  data.out_of_scope.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-slate-400 font-bold">✕</span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="italic text-slate-400">No explicit out-of-scope exclusions documented.</li>
                )}
              </ul>
            </div>
          </div>

          {/* Expected Deliverables Table */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <FileCheck2 className="w-4 h-4 text-blue-600" />
                Authoritative Expected Deliverables ({data.expected_deliverables?.length || 0})
              </h3>
              <Badge variant="low" size="xs">Preserved Source Names</Badge>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-3">Deliverable Name</th>
                    <th className="py-2.5 px-3">Owner Assigned</th>
                    <th className="py-2.5 px-3">Target Date</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.expected_deliverables?.map((del, i) => (
                    <tr key={i} className="hover:bg-slate-50 transition">
                      <td className="py-3 px-3 font-semibold text-slate-800">{del.name}</td>
                      <td className="py-3 px-3">
                        {del.owner ? (
                          <span className="inline-flex items-center gap-1 font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full">
                            <Users className="w-3 h-3 text-slate-500" />
                            {del.owner}
                          </span>
                        ) : (
                          <span className="text-slate-400 italic">Unassigned</span>
                        )}
                      </td>
                      <td className="py-3 px-3 text-slate-600 font-mono">
                        {del.deadline && del.deadline !== 'Not specified' ? del.deadline : (del.target_date && del.target_date !== 'Not specified' ? del.target_date : 'TBD')}
                      </td>
                      <td className="py-3 px-3">
                        <Badge variant={del.status?.toLowerCase().includes('complete') ? 'low' : 'medium'} size="xs">
                          {del.status || 'Active'}
                        </Badge>
                      </td>
                      <td className="py-3 px-3 text-right">
                        {del.evidence && (
                          <button
                            onClick={() => setSelectedEvidence({
                              title: del.name,
                              evidence: del.evidence,
                              filename: del?.source_document || selectedFilename,
                              source: del?.source_document || selectedFilename,
                              confidence: typeof del?.confidence === 'number' ? del.confidence : undefined,
                            })}
                            className="p-1 text-slate-400 hover:text-blue-600 rounded transition"
                          >
                            <Maximize2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Milestones & Team Responsibilities Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Milestones */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Calendar className="w-4 h-4 text-indigo-600" />
                Project Milestones & Key Deadlines
              </h3>
              <div className="space-y-2">
                {data.milestones?.map((m, idx) => (
                  <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs">
                    <div className="flex items-center justify-between font-semibold text-slate-800">
                      <span>{m.title || m.name}</span>
                      <span className="font-mono text-indigo-600 text-[11px]">{m.target_date || m.date || 'TBD'}</span>
                    </div>
                    {m.description && <p className="text-slate-500 text-[11px] mt-1">{m.description}</p>}
                  </div>
                ))}
              </div>
            </div>

            {/* Responsibilities */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Users className="w-4 h-4 text-emerald-600" />
                Team Responsibilities & Ownership
              </h3>
              <div className="space-y-2">
                {data.team_responsibilities?.map((resp, idx) => (
                  <div key={idx} className="p-3 rounded-lg border border-slate-100 bg-slate-50 text-xs flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-slate-800">
                        {resp.role ? (
                          <>
                            <span>{resp.role}</span>
                            {(resp.member || resp.person || resp.role_or_person) && (
                              <>
                                <span className="font-normal text-slate-400 mx-1.5">—</span>
                                <span className="text-slate-700 font-medium">{resp.member || resp.person || resp.role_or_person}</span>
                              </>
                            )}
                          </>
                        ) : (
                          resp.member || resp.person || resp.role_or_person || resp.name || 'Unassigned'
                        )}
                      </p>
                      <p className="text-slate-500 text-[11px]">
                        {resp.role
                          ? (resp.responsibility !== resp.role ? resp.responsibility : null)
                          : resp.responsibility}
                      </p>
                    </div>
                    {resp.deliverable && (
                      <Badge variant="info" size="xs">{resp.deliverable}</Badge>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Raw JSON Debug toggle */}
          <div className="pt-2 flex justify-end">
            <button
              onClick={() => setShowRaw(!showRaw)}
              className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
            >
              <Code className="w-3.5 h-3.5" />
              {showRaw ? 'Hide Raw JSON' : 'View Raw API Response'}
            </button>
          </div>

          {showRaw && (
            <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl text-xs font-mono overflow-x-auto">
              {JSON.stringify(data, null, 2)}
            </pre>
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
        filename={selectedEvidence?.filename}
        source={selectedEvidence?.source}
      />
    </div>
  );
}
