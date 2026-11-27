import React, { useState } from 'react';
import { 
  AlertOctagon, 
  Sparkles, 
  AlertTriangle, 
  CheckSquare, 
  HelpCircle, 
  Clock, 
  Users, 
  Maximize2, 
  RefreshCw, 
  AlertCircle,
  CheckCircle2,
  Code,
  UserX
} from 'lucide-react';
import Badge from '../components/Badge';
import EvidenceModal from '../components/EvidenceModal';
import { api } from '../services/api';
import { SAMPLE_DATASETS } from '../services/sampleData';
import { renderSafeText, getAssigneeName, isItemUnassigned } from '../utils/safeRender';

export default function BlockerAgentPage({ preloadedText }) {
  const [inputText, setInputText] = useState(preloadedText || SAMPLE_DATASETS[1].text);
  const [selectedFilename, setSelectedFilename] = useState(SAMPLE_DATASETS[1].filename);
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
      const res = await api.identifyBlockers({ text: inputText, filename: selectedFilename });
      setData(res);
    } catch (err) {
      setError(err.message || 'Blocker analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const blockersList = data?.active_blockers || data?.blockers || [];
  const pendingDecisionsList = data?.pending_decisions || [];
  const actionItemsList = data?.action_items || [];
  const delayedActivitiesList = data?.delayed_activities || [];
  const unresolvedIssuesList = data?.unresolved_issues || data?.unresolved_questions || [];

  const unassignedCount = data?.unassigned_action_items_count ?? (
    actionItemsList.filter(isItemUnassigned).length || 0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          <AlertOctagon className="w-6 h-6 text-rose-600" />
          Blocker & Action Item Identification Agent
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Specialized agent that isolates active delivery blockers, extracts pending executive decisions with designated decision-makers, catalogs unresolved questions, and flags unassigned action items.
        </p>
      </div>

      {/* Input Panel */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <label className="text-sm font-bold text-slate-800 flex items-center gap-2">
            Meeting Notes / Standup / Incident Report
          </label>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Presets:</span>
            <button
              onClick={() => {
                setInputText(SAMPLE_DATASETS[1].text);
                setSelectedFilename(SAMPLE_DATASETS[1].filename);
              }}
              className="text-xs bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-600 px-2 py-1 rounded transition cursor-pointer"
            >
              Sprint Retrospective Notes (TXT)
            </button>
            <button
              onClick={() => {
                setInputText(SAMPLE_DATASETS[3].text);
                setSelectedFilename(SAMPLE_DATASETS[3].filename);
              }}
              className="text-xs bg-slate-100 hover:bg-rose-50 hover:text-rose-700 text-slate-600 px-2 py-1 rounded transition cursor-pointer"
            >
              Task Matrix (CSV)
            </button>
          </div>
        </div>

        <textarea
          rows={6}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Paste sprint meeting minutes, blocker discussions, decision items, or unresolved questions..."
          className="w-full p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs font-mono text-slate-800 focus:outline-hidden focus:ring-2 focus:ring-rose-500 focus:bg-white leading-relaxed transition"
        />

        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">
            {inputText.length} characters • {inputText.split(/\s+/).filter(Boolean).length} words
          </span>
          <button
            onClick={handleAnalyze}
            disabled={analyzing || !inputText.trim()}
            className="px-6 py-2.5 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white font-semibold text-sm rounded-xl transition shadow-xs flex items-center gap-2 cursor-pointer"
          >
            {analyzing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Identifying Blockers...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Extract Blockers & Actions
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
          {/* Summary Metric Pills */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
              <span className="text-xs font-semibold text-slate-400">Active Blockers</span>
              <div className="flex items-center justify-between mt-1">
                <span className="text-2xl font-bold text-rose-600">{blockersList.length}</span>
                <AlertOctagon className="w-5 h-5 text-rose-400" />
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
              <span className="text-xs font-semibold text-slate-400">Pending Decisions</span>
              <div className="flex items-center justify-between mt-1">
                <span className="text-2xl font-bold text-indigo-600">{pendingDecisionsList.length}</span>
                <HelpCircle className="w-5 h-5 text-indigo-400" />
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs">
              <span className="text-xs font-semibold text-slate-400">Action Items</span>
              <div className="flex items-center justify-between mt-1">
                <span className="text-2xl font-bold text-slate-800">{actionItemsList.length}</span>
                <CheckSquare className="w-5 h-5 text-slate-400" />
              </div>
            </div>

            <div className={`rounded-xl border p-4 shadow-xs ${
              unassignedCount > 0 ? 'bg-amber-50 border-amber-300' : 'bg-white border-slate-200'
            }`}>
              <span className={`text-xs font-semibold ${unassignedCount > 0 ? 'text-amber-800' : 'text-slate-400'}`}>
                Unassigned Items
              </span>
              <div className="flex items-center justify-between mt-1">
                <span className={`text-2xl font-bold ${unassignedCount > 0 ? 'text-amber-700' : 'text-slate-800'}`}>
                  {unassignedCount}
                </span>
                <UserX className={`w-5 h-5 ${unassignedCount > 0 ? 'text-amber-600' : 'text-slate-400'}`} />
              </div>
            </div>
          </div>

          {/* Active Blockers Section */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <AlertOctagon className="w-4 h-4 text-rose-600" />
              Critical Active Blockers ({blockersList.length})
            </h3>

            {blockersList.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No critical blockers detected.</p>
            ) : (
              <div className="space-y-3">
                {blockersList.map((blk, idx) => {
                  const blockerId = blk?.blocker_id || blk?.id || `BLK-${idx + 1}`;
                  const title = blk?.title || blk?.description || `Blocker ${idx + 1}`;
                  const description = blk?.title && blk?.description && blk?.title !== blk?.description ? blk.description : null;
                  const ownerName = getAssigneeName(blk);
                  const evidenceList = blk?.supporting_evidence || blk?.evidence || [];
                  const affectedList = Array.isArray(blk?.affected_activities) ? blk.affected_activities : [];

                  return (
                    <div
                      key={blockerId || idx}
                      className="p-4 rounded-xl border border-rose-200 bg-rose-50/30 hover:bg-rose-50/60 transition space-y-2"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded">
                            {blockerId}
                          </span>
                          <span className="font-bold text-slate-900 text-sm">{renderSafeText(title)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={blk?.severity?.toLowerCase() || 'critical'} size="xs">
                            {(blk?.severity || blk?.status || 'ACTIVE').toUpperCase()}
                          </Badge>
                          {ownerName && ownerName.toLowerCase() !== 'unassigned' && (
                            <span className="text-xs text-slate-600 flex items-center gap-1 bg-white px-2 py-0.5 rounded border border-slate-200">
                              <Users className="w-3 h-3 text-slate-400" />
                              {ownerName}
                            </span>
                          )}
                        </div>
                      </div>

                      {description && (
                        <p className="text-xs text-slate-700">{renderSafeText(description)}</p>
                      )}

                      {blk?.impact && (
                        <p className="text-xs text-slate-700">
                          <strong className="text-slate-900">Impact: </strong>{renderSafeText(blk.impact)}
                        </p>
                      )}

                      {/* Affected Activities */}
                      {affectedList.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1 text-xs text-slate-600">
                          <span className="text-slate-500 font-semibold text-[11px]">Affected:</span>
                          {affectedList.map((actItem, actIdx) => (
                            <span
                              key={actItem?.activity_id || actIdx}
                              className="bg-white/80 border border-rose-200 text-rose-800 px-2 py-0.5 rounded text-[11px] font-medium"
                            >
                              {renderSafeText(actItem)}
                            </span>
                          ))}
                        </div>
                      )}

                      {evidenceList.length > 0 && (
                        <div className="pt-2 border-t border-rose-100 flex justify-end">
                          <button
                            onClick={() => setSelectedEvidence({
                              title: renderSafeText(title) || 'Blocker Evidence',
                              evidence: evidenceList,
                              filename: selectedFilename,
                              source: blk?.source_document || selectedFilename,
                              confidence: typeof blk?.confidence === 'number' ? blk.confidence : undefined,
                            })}
                            className="text-[11px] text-rose-700 hover:text-rose-900 font-semibold flex items-center gap-1 cursor-pointer"
                          >
                            <Maximize2 className="w-3 h-3" />
                            Inspect Verbatim Evidence
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Pending Decisions & Delayed Activities */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pending Decisions with Decision Makers */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-indigo-600" />
                Pending Decisions & Designated Decision Makers ({pendingDecisionsList.length})
              </h3>
              <div className="space-y-2">
                {pendingDecisionsList.length ? (
                  pendingDecisionsList.map((dec, i) => {
                    const decId = dec?.decision_id || dec?.id || `DEC-${i + 1}`;
                    const decText = dec?.description || dec?.title || dec?.decision || (typeof dec === 'string' ? dec : decId);
                    const makerName = getAssigneeName(dec);
                    const evidenceList = dec?.evidence || dec?.supporting_evidence || [];

                    return (
                      <div key={decId || i} className="p-3 rounded-lg border border-slate-200 bg-slate-50 text-xs space-y-1.5">
                        <div className="flex flex-wrap items-center justify-between gap-1.5">
                          <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                            <span className="font-mono text-[10px] text-indigo-600 bg-indigo-50 border border-indigo-100 px-1.5 py-0.5 rounded font-bold">
                              {decId}
                            </span>
                            <span>{renderSafeText(decText)}</span>
                          </div>
                          {makerName && makerName.toLowerCase() !== 'unknown' && makerName.toLowerCase() !== 'unassigned' ? (
                            <span className="font-medium text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200 text-[11px]">
                              Owner: {makerName}
                            </span>
                          ) : (
                            <span className="text-amber-600 bg-amber-50 px-2 py-0.5 rounded text-[11px] border border-amber-200">
                              Pending Owner
                            </span>
                          )}
                        </div>
                        {dec?.context && <p className="text-slate-600 text-[11px]">{renderSafeText(dec.context)}</p>}
                        {dec?.deadline && dec.deadline !== 'Not specified' && (
                          <p className="text-[10px] text-slate-400 font-mono">Needed by: {dec.deadline}</p>
                        )}
                        {evidenceList.length > 0 && (
                          <div className="pt-1 flex justify-end">
                            <button
                              onClick={() => setSelectedEvidence({
                                title: renderSafeText(decText) || 'Decision Evidence',
                                evidence: evidenceList,
                                filename: selectedFilename,
                                source: dec?.source_document || selectedFilename,
                                confidence: typeof dec?.confidence === 'number' ? dec.confidence : undefined,
                              })}
                              className="text-[10px] text-indigo-600 hover:text-indigo-800 font-semibold flex items-center gap-1 cursor-pointer"
                            >
                              <Maximize2 className="w-2.5 h-2.5" /> Verbatim Evidence
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-slate-400 italic">No pending decisions identified.</p>
                )}
              </div>
            </div>

            {/* Delayed Activities & Unresolved Questions */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-600" />
                Delayed Activities & Unresolved Questions ({delayedActivitiesList.length + unresolvedIssuesList.length})
              </h3>
              <div className="space-y-2">
                {delayedActivitiesList.map((act, i) => {
                  const actId = act?.activity_id || act?.id || `ACT-DLY-${i + 1}`;
                  const actDesc = act?.description || act?.activity || act?.name || act?.title || (typeof act === 'string' ? act : actId);
                  const reason = act?.reason || act?.delay_reason;
                  const evidenceList = act?.evidence || act?.supporting_evidence || [];

                  return (
                    <div key={actId || i} className="p-3 rounded-lg border border-amber-200 bg-amber-50/40 text-xs space-y-1.5">
                      <div className="flex items-center justify-between font-semibold text-slate-800">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded font-bold">
                            {actId}
                          </span>
                          <span>{renderSafeText(actDesc)}</span>
                        </div>
                        <Badge variant="medium" size="xs">DELAYED</Badge>
                      </div>
                      {reason && (
                        <p className="text-slate-600 text-[11px]">
                          <strong className="text-slate-700">Reason: </strong>{renderSafeText(reason)}
                        </p>
                      )}
                      {evidenceList.length > 0 && (
                        <div className="pt-1 flex justify-end">
                          <button
                            onClick={() => setSelectedEvidence({
                              title: renderSafeText(actDesc) || 'Delayed Activity Evidence',
                              evidence: evidenceList,
                              filename: selectedFilename,
                              source: act?.source_document || selectedFilename,
                              confidence: typeof act?.confidence === 'number' ? act.confidence : undefined,
                            })}
                            className="text-[10px] text-amber-700 hover:text-amber-900 font-semibold flex items-center gap-1 cursor-pointer"
                          >
                            <Maximize2 className="w-2.5 h-2.5" /> Verbatim Evidence
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}

                {unresolvedIssuesList.map((q, i) => {
                  const qId = q?.issue_id || q?.id || `ISS-${i + 1}`;
                  const qText = q?.title || q?.question || q?.description || (typeof q === 'string' ? q : qId);
                  const evidenceList = q?.evidence || q?.supporting_evidence || [];

                  return (
                    <div key={qId || i} className="p-3 rounded-lg border border-slate-200 bg-slate-50 text-xs space-y-1.5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5 font-semibold text-slate-700">
                          <span className="font-mono text-[10px] text-slate-500 bg-slate-200/70 px-1.5 py-0.5 rounded font-bold">
                            {qId}
                          </span>
                          <span>? {renderSafeText(qText)}</span>
                        </div>
                        {q?.status && (
                          <Badge variant="info" size="xs">
                            {renderSafeText(q.status).toUpperCase()}
                          </Badge>
                        )}
                      </div>
                      {evidenceList.length > 0 && (
                        <div className="pt-1 flex justify-end">
                          <button
                            onClick={() => setSelectedEvidence({
                              title: renderSafeText(qText) || 'Unresolved Issue Evidence',
                              evidence: evidenceList,
                              filename: selectedFilename,
                              source: q?.source_document || selectedFilename,
                              confidence: typeof q?.confidence === 'number' ? q.confidence : undefined,
                            })}
                            className="text-[10px] text-slate-500 hover:text-slate-700 font-semibold flex items-center gap-1 cursor-pointer"
                          >
                            <Maximize2 className="w-2.5 h-2.5" /> Verbatim Evidence
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}

                {delayedActivitiesList.length === 0 && unresolvedIssuesList.length === 0 && (
                  <p className="text-xs text-slate-400 italic">No delayed activities or unresolved questions identified.</p>
                )}
              </div>
            </div>
          </div>

          {/* Action Items Table */}
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2 mb-4">
              <CheckSquare className="w-4 h-4 text-emerald-600" />
              Action Items & Assigned Follow-ups ({actionItemsList.length})
            </h3>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-semibold">
                    <th className="py-2.5 px-3">ID</th>
                    <th className="py-2.5 px-3">Action Description</th>
                    <th className="py-2.5 px-3">Assignee</th>
                    <th className="py-2.5 px-3">Due Date</th>
                    <th className="py-2.5 px-3">Priority</th>
                    <th className="py-2.5 px-3 text-right">Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {actionItemsList.map((item, idx) => {
                    const itemId = item?.action_id || item?.id || `ACT-${idx + 1}`;
                    const itemDesc = item?.description || item?.action || (typeof item === 'string' ? item : itemId);
                    const unassigned = isItemUnassigned(item);
                    const assignee = getAssigneeName(item);
                    const dueDate = item?.deadline || item?.due_date || item?.target_date || 'TBD';
                    const evidenceList = item?.supporting_evidence || item?.evidence || [];

                    return (
                      <tr key={itemId || idx} className="hover:bg-slate-50 transition">
                        <td className="py-3 px-3 font-mono text-[11px] text-slate-400 font-semibold">
                          {itemId}
                        </td>
                        <td className="py-3 px-3 font-semibold text-slate-800">
                          {renderSafeText(itemDesc)}
                        </td>
                        <td className="py-3 px-3">
                          {unassigned ? (
                            <span className="inline-flex items-center gap-1 font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full text-[11px]">
                              <UserX className="w-3 h-3" /> Unassigned
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded-full text-[11px]">
                              <Users className="w-3 h-3 text-slate-500" /> {assignee}
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-3 font-mono text-slate-600">
                          {dueDate !== 'Not specified' ? dueDate : 'TBD'}
                        </td>
                        <td className="py-3 px-3">
                          <Badge variant={item?.priority?.toLowerCase() || 'medium'} size="xs">
                            {(item?.priority || item?.current_status || 'NORMAL').toUpperCase()}
                          </Badge>
                        </td>
                        <td className="py-3 px-3 text-right">
                          {evidenceList.length > 0 && (
                            <button
                              onClick={() => setSelectedEvidence({
                                title: renderSafeText(itemDesc),
                                evidence: evidenceList,
                                filename: item?.source_document || selectedFilename,
                                source: item?.source_document || selectedFilename,
                                confidence: typeof item?.confidence === 'number' ? item.confidence : undefined,
                              })}
                              className="p-1 text-slate-400 hover:text-rose-600 rounded transition cursor-pointer"
                              title="Inspect Evidence"
                            >
                              <Maximize2 className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
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
