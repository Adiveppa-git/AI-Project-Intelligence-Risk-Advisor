import React, { useState, useMemo } from 'react';
import { 
  ShieldAlert, 
  Sparkles, 
  AlertTriangle, 
  TrendingDown, 
  Clock, 
  DollarSign, 
  Cpu, 
  Users, 
  Maximize2, 
  RefreshCw, 
  AlertCircle,
  Code
} from 'lucide-react';
import Badge from '../components/Badge';
import EvidenceModal from '../components/EvidenceModal';
import { api } from '../services/api';
import { SAMPLE_DATASETS } from '../services/sampleData';

export default function RiskAgentPage({ preloadedText }) {
  const [inputText, setInputText] = useState(preloadedText || SAMPLE_DATASETS[2].text);
  const [selectedFilename, setSelectedFilename] = useState(SAMPLE_DATASETS[2].filename);
  const [analyzing, setAnalyzing] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selectedEvidence, setSelectedEvidence] = useState(null);
  const [showRaw, setShowRaw] = useState(false);

  // Compute category counts directly from the final risks array to guarantee strict consistency
  const categoryCounts = useMemo(() => {
    if (!data?.risks) return {};
    return data.risks.reduce((acc, r) => {
      const cat = r.category || 'Other';
      acc[cat] = (acc[cat] || 0) + 1;
      return acc;
    }, {});
  }, [data?.risks]);

  const handleAnalyze = async () => {
    if (!inputText.trim()) return;
    try {
      setAnalyzing(true);
      setError(null);
      const res = await api.detectRisks({ text: inputText, filename: selectedFilename });
      setData(res);
    } catch (err) {
      setError(err.message || 'Risk analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const getCategoryIcon = (category = '') => {
    const c = category.toLowerCase();
    if (c.includes('sched')) return <Clock className="w-4 h-4 text-amber-500" />;
    if (c.includes('budg')) return <DollarSign className="w-4 h-4 text-rose-500" />;
    if (c.includes('depend')) return <Cpu className="w-4 h-4 text-purple-500" />;
    if (c.includes('resourc')) return <Users className="w-4 h-4 text-blue-500" />;
    return <AlertTriangle className="w-4 h-4 text-orange-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-amber-600" />
          Risk Detection & Delivery Forecasting Agent
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Specialized risk detection classifier that extracts individual risk findings across 5 core categories: <strong>Schedule, Budget, Dependency, Resource, and Delivery</strong>. Generates delivery forecasts and flags critical resource bottlenecks.
        </p>
      </div>

      {/* Input Panel */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <label className="text-sm font-bold text-slate-800 flex items-center gap-2">
            Project Risk Log / Status Report
          </label>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Presets:</span>
            <button
              onClick={() => {
                setInputText(SAMPLE_DATASETS[2].text);
                setSelectedFilename(SAMPLE_DATASETS[2].filename);
              }}
              className="text-xs bg-slate-100 hover:bg-amber-50 hover:text-amber-700 text-slate-600 px-2 py-1 rounded transition"
            >
              Risk & Progress Report (DOCX)
            </button>
            <button
              onClick={() => {
                setInputText(SAMPLE_DATASETS[0].text);
                setSelectedFilename(SAMPLE_DATASETS[0].filename);
              }}
              className="text-xs bg-slate-100 hover:bg-amber-50 hover:text-amber-700 text-slate-600 px-2 py-1 rounded transition"
            >
              Enterprise Charter
            </button>
          </div>
        </div>

        <textarea
          rows={6}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste status report, schedule updates, budget logs, or resource allocations..."
          className="w-full p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-amber-500 focus:bg-white leading-relaxed transition"
        />

        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {inputText.length} characters • {inputText.split(/\s+/).filter(Boolean).length} words
          </span>
          <button
            onClick={handleAnalyze}
            disabled={analyzing || !inputText.trim()}
            className="px-6 py-2.5 bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition shadow-xs flex items-center gap-2"
          >
            {analyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Detecting Risks...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Detect Risks & Forecast Delivery
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

      {/* Analysis Results */}
      {data && (
        <div className="space-y-6">
          {/* Top Risk Level & Delivery Concerns Banner */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Overall Risk Assessment</span>
                <div className="flex items-center gap-3">
                  <Badge variant={data.overall_risk_level?.toLowerCase()} size="lg">
                    {data.overall_risk_level?.toUpperCase()} RISK
                  </Badge>
                  <span className="text-sm font-semibold text-slate-800">
                    {data.risks?.length || 0} Individual Risk Findings Identified
                  </span>
                </div>
                {data.delivery_concerns_summary && (
                  <p className="text-xs text-slate-600 mt-1 font-medium leading-relaxed">
                    {data.delivery_concerns_summary}
                  </p>
                )}
              </div>

              {/* Potential Bottlenecks Pill */}
              {data.potential_bottlenecks?.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-3.5 max-w-md text-xs shrink-0">
                  <span className="font-bold text-amber-800 flex items-center gap-1.5 mb-1">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                    Identified Bottlenecks & Constraints
                  </span>
                  <ul className="space-y-1 text-amber-900">
                    {data.potential_bottlenecks.map((b, i) => (
                      <li key={i}>• {b}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Category Breakdown Chips */}
            <div className="flex flex-wrap items-center gap-2 pt-3 border-t border-slate-100 text-xs text-slate-600">
              <span className="font-semibold text-slate-500">Active Risk Categories:</span>
              {(categoryCounts['Schedule'] || 0) > 0 && (
                <span className="bg-amber-50 text-amber-700 px-2.5 py-0.5 rounded-full border border-amber-200 font-medium">
                  {categoryCounts['Schedule']} Schedule
                </span>
              )}
              {(categoryCounts['Budget'] || 0) > 0 && (
                <span className="bg-rose-50 text-rose-700 px-2.5 py-0.5 rounded-full border border-rose-200 font-medium">
                  {categoryCounts['Budget']} Budget
                </span>
              )}
              {(categoryCounts['Dependency'] || 0) > 0 && (
                <span className="bg-purple-50 text-purple-700 px-2.5 py-0.5 rounded-full border border-purple-200 font-medium">
                  {categoryCounts['Dependency']} Dependency
                </span>
              )}
              {(categoryCounts['Resource'] || 0) > 0 && (
                <span className="bg-blue-50 text-blue-700 px-2.5 py-0.5 rounded-full border border-blue-200 font-medium">
                  {categoryCounts['Resource']} Resource
                </span>
              )}
              {(categoryCounts['Bottleneck'] || 0) > 0 && (
                <span className="bg-orange-50 text-orange-700 px-2.5 py-0.5 rounded-full border border-orange-200 font-medium">
                  {categoryCounts['Bottleneck']} Bottleneck
                </span>
              )}
              {(categoryCounts['Delivery'] || 0) > 0 && (
                <span className="bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded-full border border-emerald-200 font-medium">
                  {categoryCounts['Delivery']} Delivery
                </span>
              )}
            </div>
          </div>

          {/* Categorized Risk Findings List */}
          <div className="space-y-3">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              Detailed Risk Findings by Category
            </h3>

            <div className="grid grid-cols-1 gap-3">
              {data.risks?.map((risk, idx) => (
                <div
                  key={idx}
                  className="bg-white rounded-xl border border-slate-200 p-5 hover:border-amber-300 transition-all shadow-xs space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      {getCategoryIcon(risk.category)}
                      <span className="font-bold text-slate-900 text-sm">{risk.title}</span>
                      <span className="font-mono text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
                        {risk.risk_id || risk.id || `RSK-${idx + 1}`}
                      </span>
                      {(risk.related_blocker_id || risk.related_blocker_ids?.length > 0) && (
                        <span className="font-mono text-[10px] text-rose-700 bg-rose-50 border border-rose-200 px-1.5 py-0.5 rounded font-bold">
                          Blocker: {risk.related_blocker_id || risk.related_blocker_ids[0]}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="info" size="xs">{risk.category?.toUpperCase()}</Badge>
                      <Badge variant={risk.severity?.toLowerCase()} size="xs">
                        {risk.severity?.toUpperCase()}
                      </Badge>
                    </div>
                  </div>

                  <p className="text-xs text-slate-700 leading-relaxed">
                    {risk.description}
                  </p>

                  {/* Multi-document Provenance Tag */}
                  {risk.merged_sources?.length > 1 && (
                    <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-slate-500 font-mono">
                      <span className="text-slate-400 font-sans">Merged across {risk.merged_sources.length} sources:</span>
                      {risk.merged_sources.map((src, si) => (
                        <span key={si} className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded text-[10px]">
                          {src}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Potential Impact */}
                  {risk.potential_impact && (
                    <div className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                      <span className="font-semibold text-slate-700">Potential Impact: </span>
                      <span>{risk.potential_impact}</span>
                    </div>
                  )}

                  {/* Verbatim Evidence & Mitigation */}
                  <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3 text-xs">
                    <div className="flex items-start gap-2 text-slate-600 max-w-xl">
                      <span className="font-semibold text-slate-700 shrink-0">Mitigation:</span>
                      <span className="text-slate-800 font-medium">
                        {risk.suggested_mitigation || risk.mitigation || 'Review and track risk mitigation with team lead.'}
                      </span>
                    </div>
                    {(risk.supporting_evidence?.length > 0 || risk.evidence?.length > 0) && (
                      <button
                        onClick={() => setSelectedEvidence({
                          title: risk.title,
                          evidence: risk.supporting_evidence || risk.evidence,
                          filename: risk?.source_document || selectedFilename,
                          source: risk?.source_document || selectedFilename,
                          confidence: typeof risk?.confidence === 'number' ? risk.confidence : undefined,
                        })}
                        className="text-amber-600 hover:text-amber-800 font-semibold flex items-center gap-1 text-[11px] shrink-0"
                      >
                        <Maximize2 className="w-3 h-3" />
                        Verbatim Source Evidence
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Delivery Forecasts */}
          {(data.delayed_milestones_forecast?.length > 0 || data.delivery_forecasts?.length > 0) && (
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-indigo-600" />
                Delivery Forecasts & Confidence
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(data.delayed_milestones_forecast || data.delivery_forecasts).map((f, i) => (
                  <div key={i} className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-2">
                    <div className="flex items-center justify-between font-semibold text-slate-800">
                      <span className="text-slate-900 font-bold">{f.milestone_name || f.deliverable || f.name}</span>
                      <div className="flex items-center gap-2">
                        {f.delay_severity && (
                          <Badge variant={f.delay_severity.toLowerCase()} size="xs">
                            {f.delay_severity}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-500 font-mono">
                      <span>Target: <strong className="text-slate-700">{f.actual_deadline && f.actual_deadline !== 'Not specified' ? f.actual_deadline : 'Date not specified'}</strong></span>
                      {f.forecasted_date && f.forecasted_date !== 'Not specified' && f.forecasted_date !== 'Date not specified' && f.forecasted_date !== f.actual_deadline && (
                        <span>Forecast: <strong className="text-indigo-600">{f.forecasted_date}</strong></span>
                      )}
                    </div>
                    <p className="text-slate-600 text-[11px] leading-relaxed">{f.predicted_delay_reason || f.notes || f.rationale}</p>
                    {f.confidence !== undefined && (
                      <div className="text-[10px] text-slate-400">
                        Confidence: {(f.confidence * 100).toFixed(0)}%
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Raw JSON Debug */}
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
