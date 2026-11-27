import React, { useState } from 'react';
import { 
  Sparkles, 
  Layers, 
  Activity, 
  ShieldAlert, 
  FileCheck2, 
  AlertOctagon, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Sliders, 
  Copy, 
  Check, 
  Code,
  ArrowRight,
  TrendingUp,
  Cpu,
  Clock,
  HelpCircle,
  Calendar,
  User,
  AlertCircle
} from 'lucide-react';
import Badge from '../components/Badge';
import { api } from '../services/api';
import { SAMPLE_DATASETS } from '../services/sampleData';
import { renderSafeText } from '../utils/safeRender';

export default function MultiAgentPage({ preloadedText, onNavigate }) {
  // Default to full integrated corpus preset (index 4) if available, otherwise index 0
  const defaultDoc = SAMPLE_DATASETS.find(d => d.id === 'unified_corpus') || SAMPLE_DATASETS[0];
  const [inputText, setInputText] = useState(preloadedText || defaultDoc.text);
  const [selectedFilename, setSelectedFilename] = useState(defaultDoc.filename);
  const [topK, setTopK] = useState(3);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('summary');
  const [showRaw, setShowRaw] = useState(false);

  const handleRunAnalysis = async () => {
    if (!inputText.trim()) return;
    try {
      setAnalyzing(true);
      setError(null);
      const res = await api.analyzeProject({
        text: inputText,
        top_k: topK,
        filename: selectedFilename,
      });
      setResult(res);
      setActiveTab('summary');
    } catch (err) {
      setError(err.message || 'Complete analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  // Extract structured findings safely with dual-schema compatibility
  const scope = result?.scope_and_deliverables || result?.scope_analysis || {};
  const risk = result?.risk_and_forecasting || result?.risk_analysis || {};
  const blocker = result?.blockers_and_actions || result?.blocker_analysis || {};

  const deliverables = scope.expected_deliverables || [];
  const milestones = scope.milestones || [];
  const inScope = scope.in_scope || [];
  const outOfScope = scope.out_of_scope || [];
  const projectTitle = scope.project_title || result?.project_title || 'Project Intelligence Analysis';

  const risks = risk.risks || [];
  const riskLevel = risk.overall_risk_level || 'Low';
  const riskSummary = risk.delivery_concerns_summary || 'No critical delivery concerns detected based on evidence.';
  const delayedForecasts = risk.delayed_milestones_forecast || [];

  const blockers = blocker.active_blockers || blocker.blockers || [];
  const actionItems = blocker.action_items || [];
  const pendingDecisions = blocker.pending_decisions || [];
  const delayedActivities = blocker.delayed_activities || [];
  const unresolvedIssues = blocker.unresolved_issues || blocker.unresolved_questions || [];

  const partialFailures = result?.partial_failures || result?.partial_failure_details || [];
  const hasFailures = partialFailures.length > 0 || Boolean(result?.has_partial_failures);

  const healthStatus = result?.project_health || result?.overall_health_status || 'Healthy';

  // Compute a valid health score ensuring it is never NaN, null, or undefined
  const healthScore = typeof result?.overall_health_score === 'number' && !isNaN(result.overall_health_score)
    ? result.overall_health_score
    : (healthStatus === 'Healthy' ? 92 : healthStatus === 'Needs Attention' ? 75 : healthStatus === 'At Risk' ? 52 : 32);

  // Safe assessment date formatting (never displays 'Invalid Date')
  const rawDate = result?.generated_at || result?.timestamp;
  const parsedDate = rawDate ? new Date(rawDate) : new Date();
  const validDate = !isNaN(parsedDate.getTime()) ? parsedDate : new Date();
  const displayTime = validDate.toLocaleTimeString();
  const displayFullDate = validDate.toLocaleString();

  const handleCopyReport = () => {
    if (!result) return;
    const report = `AI PROJECT RISK ADVISOR - EXECUTIVE REPORT
Project Health Score: ${healthScore}/100 (${healthStatus})
Generated: ${displayFullDate}

EXECUTIVE SUMMARY:
${result.executive_summary || 'Executive summary unavailable.'}

KEY RECOMMENDATIONS:
${result.key_recommendations?.map((r, i) => `${i + 1}. ${r}`).join('\n') || 'None'}

SCOPE DELIVERABLES (${deliverables.length} items):
${deliverables.map(d => `- ${d.name} (Owner: ${d.owner || 'Unassigned'}, Deadline: ${d.deadline || d.target_date || 'Not specified'})`).join('\n') || 'None'}

IDENTIFIED RISKS (${riskLevel.toUpperCase()} RISK, ${risks.length} findings):
${risks.map(r => `[${(r.category || 'General').toUpperCase()}] ${r.title} - ${r.description}`).join('\n') || 'None'}

BLOCKERS (${blockers.length} active):
${blockers.map(b => `[${(b.severity || 'High').toUpperCase()}] ${renderSafeText(b.title || b.description)}`).join('\n') || 'None'}

ACTION ITEMS (${actionItems.length} items):
${actionItems.map(a => `- ${a.description} (Owner: ${a.assigned_person || a.assignee || 'Unassigned'}, Priority: ${a.priority || 'Medium'}, Deadline: ${a.deadline || a.due_date || 'Not specified'})`).join('\n') || 'None'}

PENDING DECISIONS (${pendingDecisions.length} decisions):
${pendingDecisions.map(d => `- ${d.description || d.title} (Decision Maker: ${d.decision_maker || 'Unknown'}, Deadline: ${d.deadline || 'Not specified'})`).join('\n') || 'None'}
`;
    navigator.clipboard.writeText(report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const getHealthColor = (score) => {
    if (score >= 80) return { text: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', bar: 'bg-emerald-500' };
    if (score >= 60) return { text: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', bar: 'bg-amber-500' };
    return { text: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-200', bar: 'bg-rose-500' };
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-indigo-600" />
          Autonomous Multi-Agent Orchestrator
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Executes the <strong>Scope Agent, Risk Agent, and Blocker Agent</strong> concurrently. Aggregates findings, computes a standardized 0-100 project health score, and synthesizes executive recommendations with partial failure resilience.
        </p>
      </div>

      {/* Input Box */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <label className="text-sm font-bold text-slate-800 flex items-center gap-2">
            Project Input Corpus for Full Multi-Agent Evaluation
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-slate-400">Presets:</span>
            {SAMPLE_DATASETS.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setInputText(s.text);
                  setSelectedFilename(s.filename);
                }}
                className={`text-xs px-2.5 py-1 rounded transition cursor-pointer font-medium ${
                  s.id === 'unified_corpus'
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs'
                    : 'bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-600'
                }`}
                title={s.name}
              >
                {s.id === 'unified_corpus' ? '★ FULL CORPUS (All 4)' : s.format}
              </button>
            ))}
          </div>
        </div>

        <textarea
          rows={7}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste comprehensive project documentation, charters, meeting notes, risk logs, or multi-format text..."
          className="w-full p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:bg-white leading-relaxed transition"
        />

        <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
          <div className="flex items-center gap-3 text-xs text-slate-600">
            <Sliders className="w-3.5 h-3.5" />
            <span>RAG Context Chunks (top_k):</span>
            <input
              type="range"
              min="1"
              max="8"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-20 accent-indigo-600 cursor-pointer"
            />
            <span className="font-mono font-bold text-indigo-600">{topK}</span>
            <span className="text-slate-400 text-[11px] ml-2">
              Source file: <span className="font-mono text-slate-600">{selectedFilename}</span>
            </span>
          </div>

          <button
            onClick={handleRunAnalysis}
            disabled={analyzing || !inputText.trim()}
            className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition shadow-md flex items-center gap-2 cursor-pointer"
          >
            {analyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Orchestrating 3 Agents in Parallel...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-yellow-300" />
                Run Complete Multi-Agent Analysis
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

      {/* Synthesis Results Display */}
      {result && (
        <div className="space-y-6">
          {/* Executive Overview Banner */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              {/* Health Score Dial */}
              <div className="flex items-center gap-4">
                <div className={`w-20 h-20 rounded-2xl flex flex-col items-center justify-center border shadow-xs ${getHealthColor(healthScore).bg} ${getHealthColor(healthScore).border}`}>
                  <span className={`text-2xl font-black ${getHealthColor(healthScore).text}`}>
                    {healthScore}
                  </span>
                  <span className="text-[10px] font-bold text-slate-500 uppercase">/ 100</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <Badge variant={healthScore >= 80 ? 'healthy' : healthScore >= 60 ? 'warning' : 'critical'} size="md">
                      {healthStatus.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-slate-400 font-mono">
                      Assessment: {displayTime}
                    </span>
                  </div>
                  <h2 className="text-base font-bold text-slate-900 mt-1">
                    {projectTitle}
                  </h2>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyReport}
                  className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs rounded-lg transition flex items-center gap-1.5 cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'Copied Full Report' : 'Copy Executive Report'}
                </button>
              </div>
            </div>

            {/* Partial Failures Notification if any */}
            {hasFailures && (
              <div className="p-3 bg-amber-50 border border-amber-300 rounded-lg text-amber-900 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>
                  Partial failure detected during multi-agent orchestration. Resilient fallback was applied: {partialFailures.join(', ')}
                </span>
              </div>
            )}

            {/* Executive Summary Paragraph */}
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">
                Executive Synthesis
              </h3>
              <p className="text-sm text-slate-800 leading-relaxed font-sans">
                {result.executive_summary}
              </p>
            </div>

            {/* Key Recommendations */}
            {result.key_recommendations?.length > 0 && (
              <div className="bg-indigo-50/60 rounded-xl border border-indigo-100 p-4 space-y-2">
                <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
                  Key Strategic Recommendations
                </h4>
                <ul className="space-y-1.5 text-xs text-indigo-950">
                  {result.key_recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="font-bold text-indigo-600">#{i + 1}</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Deep-Dive Agent Navigation Tabs */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
            <div className="flex border-b border-slate-200 gap-4 overflow-x-auto">
              <button
                onClick={() => setActiveTab('summary')}
                className={`pb-2.5 text-xs font-bold border-b-2 transition whitespace-nowrap cursor-pointer ${
                  activeTab === 'summary'
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                Synthesized Overview
              </button>
              <button
                onClick={() => setActiveTab('scope')}
                className={`pb-2.5 text-xs font-bold border-b-2 transition flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeTab === 'scope'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <FileCheck2 className="w-3.5 h-3.5" />
                Scope Agent Findings ({deliverables.length})
              </button>
              <button
                onClick={() => setActiveTab('risks')}
                className={`pb-2.5 text-xs font-bold border-b-2 transition flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeTab === 'risks'
                    ? 'border-amber-600 text-amber-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                Risk Agent Findings ({risks.length})
              </button>
              <button
                onClick={() => setActiveTab('blockers')}
                className={`pb-2.5 text-xs font-bold border-b-2 transition flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                  activeTab === 'blockers'
                    ? 'border-rose-600 text-rose-600'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <AlertOctagon className="w-3.5 h-3.5" />
                Blocker Agent Findings ({blockers.length})
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === 'summary' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div className="p-4 rounded-xl border border-blue-200 bg-blue-50/30 text-xs space-y-2">
                  <div className="flex items-center justify-between font-bold text-blue-900">
                    <span>Scope Extraction</span>
                    <Badge variant="low" size="xs">{deliverables.length} Deliverables</Badge>
                  </div>
                  <p className="text-slate-700">
                    <strong>Project:</strong> {projectTitle}
                  </p>
                  <p className="text-slate-600">
                    {deliverables.length} Deliverables, {milestones.length} Milestones, {inScope.length} In-scope items.
                  </p>
                </div>

                <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/30 text-xs space-y-2">
                  <div className="flex items-center justify-between font-bold text-amber-900">
                    <span>Risk Forecast</span>
                    <Badge variant={riskLevel.toLowerCase() === 'critical' ? 'critical' : riskLevel.toLowerCase() === 'high' ? 'critical' : 'warning'} size="xs">
                      {riskLevel.toUpperCase()}
                    </Badge>
                  </div>
                  <p className="text-slate-700 font-medium">
                    {risks.length} Risk Findings across core categories.
                  </p>
                  <p className="text-slate-600 text-[11px] leading-relaxed">
                    {riskSummary}
                  </p>
                </div>

                <div className="p-4 rounded-xl border border-rose-200 bg-rose-50/30 text-xs space-y-2">
                  <div className="flex items-center justify-between font-bold text-rose-900">
                    <span>Blockers & Actions</span>
                    <Badge variant={blockers.length > 0 ? 'critical' : 'healthy'} size="xs">
                      {blockers.length} BLOCKERS
                    </Badge>
                  </div>
                  <p className="text-slate-700">
                    {actionItems.length} Action Items, {pendingDecisions.length} Decisions, {delayedActivities.length} Delayed.
                  </p>
                  <p className="text-slate-600 text-[11px]">
                    Owners and designated decision-makers cross-referenced without hallucination.
                  </p>
                </div>
              </div>
            )}

            {activeTab === 'scope' && (
              <div className="space-y-4 pt-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-800 pb-2 border-b border-slate-100">
                  <span>Project Scope: <strong className="text-blue-700">{projectTitle}</strong></span>
                  <span className="text-slate-500 font-mono">{deliverables.length} Deliverables • {milestones.length} Milestones</span>
                </div>
                {deliverables.length === 0 ? (
                  <p className="text-xs text-slate-400 italic py-4 text-center">No deliverables found in the provided input.</p>
                ) : (
                  <div className="divide-y divide-slate-100 text-xs">
                    {deliverables.map((d, i) => (
                      <div key={d.deliverable_id || i} className="py-2.5 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[10px] text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded font-bold">
                            {d.deliverable_id || `DEL-${i + 1}`}
                          </span>
                          <span className="font-medium text-slate-800">{d.name}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-500 font-mono text-[11px]">
                            {d.deadline && d.deadline !== 'Not specified' ? d.deadline : d.target_date || 'No deadline'}
                          </span>
                          <span className="text-slate-600 font-medium bg-slate-100 px-2 py-0.5 rounded text-[11px]">
                            {d.owner || 'Unassigned'}
                          </span>
                          <Badge variant={d.status?.toLowerCase().includes('complete') ? 'healthy' : 'medium'} size="xs">
                            {d.status || 'Pending'}
                          </Badge>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'risks' && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-800 pb-2 border-b border-slate-100">
                  <span>Overall Risk Level: <Badge variant={riskLevel.toLowerCase() === 'critical' ? 'critical' : 'warning'} size="xs">{riskLevel.toUpperCase()}</Badge></span>
                  <span className="text-slate-500 font-mono">{risks.length} Risk Findings Identified</span>
                </div>
                {risks.length === 0 ? (
                  <p className="text-xs text-slate-400 italic py-4 text-center">No active risk findings detected.</p>
                ) : (
                  <div className="grid grid-cols-1 gap-2.5">
                    {risks.map((r, i) => (
                      <div key={r.risk_id || i} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1.5">
                        <div className="flex items-center justify-between font-semibold text-slate-800">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[10px] text-amber-800 bg-amber-100 px-1.5 py-0.5 rounded font-bold">
                              {r.risk_id || `RSK-${i + 1}`}
                            </span>
                            <span>{r.title}</span>
                            {r.category && (
                              <Badge variant="info" size="xs">{r.category}</Badge>
                            )}
                            {(r.related_blocker_id || r.related_blocker_ids?.length > 0) && (
                              <span className="font-mono text-[10px] text-rose-700 bg-rose-100 px-1.5 py-0.5 rounded font-bold">
                                Blocker: {r.related_blocker_id || r.related_blocker_ids[0]}
                              </span>
                            )}
                          </div>
                          <Badge variant={r.severity?.toLowerCase() === 'critical' ? 'critical' : r.severity?.toLowerCase() === 'high' ? 'warning' : 'medium'} size="xs">
                            {r.severity}
                          </Badge>
                        </div>
                        <p className="text-slate-600 text-[11px]">{r.description}</p>
                        {r.suggested_mitigation && (
                          <p className="text-[11px] text-slate-700 bg-white p-2 rounded border border-slate-100">
                            <strong>Mitigation:</strong> {r.suggested_mitigation}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'blockers' && (
              <div className="space-y-4 pt-2">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-800 pb-2 border-b border-slate-100">
                  <span>Blockers & Action Execution</span>
                  <span className="text-slate-500 font-mono">
                    {blockers.length} Blockers • {actionItems.length} Actions • {pendingDecisions.length} Decisions
                  </span>
                </div>

                {/* Active Blockers */}
                {blockers.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-rose-800 uppercase tracking-wider flex items-center gap-1.5">
                      <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
                      Active Blockers ({blockers.length})
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                      {blockers.map((b, i) => (
                        <div key={b?.blocker_id || b?.id || i} className="p-3 bg-rose-50/50 rounded-lg border border-rose-200 text-xs space-y-1">
                          <div className="flex items-center justify-between font-semibold text-slate-800">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[10px] text-rose-700 bg-rose-100 px-1.5 py-0.5 rounded font-bold">
                                {b?.blocker_id || `BLK-${i + 1}`}
                              </span>
                              <span>{renderSafeText(b?.title || b?.description || `Blocker ${i + 1}`)}</span>
                              {(b?.related_risk_id || b?.related_risk_ids?.length > 0) && (
                                <span className="font-mono text-[10px] text-amber-800 bg-amber-100 px-1.5 py-0.5 rounded font-bold">
                                  Risk: {b?.related_risk_id || b?.related_risk_ids[0]}
                                </span>
                              )}
                            </div>
                            <Badge variant={b?.severity?.toLowerCase() === 'critical' ? 'critical' : 'high'} size="xs">
                              {b?.severity || b?.impact_severity || 'HIGH'}
                            </Badge>
                          </div>
                          {b?.description && b?.title && <p className="text-slate-600 text-[11px]">{renderSafeText(b.description)}</p>}
                          {b?.assigned_owner && b.assigned_owner !== 'Unassigned' && (
                            <span className="text-[10px] text-slate-500">Owner: {b.assigned_owner}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Action Items */}
                {actionItems.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Action Items ({actionItems.length})
                    </h4>
                    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 text-[11px]">
                          <tr>
                            <th className="py-2 px-3">Action Description</th>
                            <th className="py-2 px-3">Assignee</th>
                            <th className="py-2 px-3">Deadline</th>
                            <th className="py-2 px-3 text-right">Priority</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {actionItems.map((act, i) => (
                            <tr key={act.action_id || i} className="hover:bg-slate-50/50">
                              <td className="py-2 px-3 font-medium text-slate-800">{act.description}</td>
                              <td className="py-2 px-3 text-slate-600 font-mono">{act.assigned_person || act.assignee || 'Unassigned'}</td>
                              <td className="py-2 px-3 text-slate-500 font-mono">{act.deadline || act.due_date || 'Not specified'}</td>
                              <td className="py-2 px-3 text-right">
                                <Badge variant={act.priority?.toLowerCase() === 'critical' ? 'critical' : 'medium'} size="xs">
                                  {act.priority || 'Medium'}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Pending Decisions */}
                {pendingDecisions.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <h4 className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
                      <HelpCircle className="w-3.5 h-3.5 text-indigo-600" />
                      Pending Decisions ({pendingDecisions.length})
                    </h4>
                    <div className="grid grid-cols-1 gap-2">
                      {pendingDecisions.map((dec, i) => (
                        <div key={dec.decision_id || i} className="p-3 bg-indigo-50/40 rounded-lg border border-indigo-200 text-xs space-y-1">
                          <div className="flex items-center justify-between font-semibold text-slate-800">
                            <span>{dec.description || dec.title}</span>
                            <span className="text-indigo-700 font-mono text-[11px]">{dec.deadline || 'Not specified'}</span>
                          </div>
                          <p className="text-slate-600 text-[11px]">Decision Maker: <strong>{dec.decision_maker || 'Unknown'}</strong></p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Raw JSON Toggle */}
          <div className="pt-2 flex justify-end">
            <button
              onClick={() => setShowRaw(!showRaw)}
              className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1 cursor-pointer"
            >
              <Code className="w-3.5 h-3.5" />
              {showRaw ? 'Hide Raw JSON' : 'View Raw API Response'}
            </button>
          </div>

          {showRaw && (
            <pre className="p-4 bg-slate-900 text-slate-100 rounded-xl text-xs font-mono overflow-x-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
