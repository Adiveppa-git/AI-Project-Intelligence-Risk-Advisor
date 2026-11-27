import React from 'react';
import { X, FileText, FileQuestion } from 'lucide-react';
import Badge from './Badge';
import {
  isValidFilename,
  getFileFormatBadge,
  resolveSourceFilename,
} from '../utils/evidenceProvenance';

export { isValidFilename, getFileFormatBadge, resolveSourceFilename };

export default function EvidenceModal({
  isOpen,
  onClose,
  evidence = [],
  title = 'Supporting Document Evidence',
  source,
  filename: modalFilename,
  confidence: modalConfidence,
}) {
  if (!isOpen) return null;

  const evidenceList = Array.isArray(evidence) ? evidence : (evidence ? [evidence] : []);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden transform transition-all animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-800 text-sm">
                {typeof title === 'string' ? title : 'Supporting Document Evidence'}
              </h3>
              <p className="text-xs text-slate-400">
                {evidenceList.length} evidence item{evidenceList.length === 1 ? '' : 's'} recorded from source files
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 max-h-[60vh] overflow-y-auto space-y-4">
          {evidenceList.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-6">No specific source excerpts recorded.</p>
          ) : (
            evidenceList.map((ev, idx) => {
              const isString = typeof ev === 'string';
              const displayFilename = resolveSourceFilename(ev, modalFilename, source);
              const isAvailable = displayFilename !== 'Source filename unavailable';
              const formatBadge = isAvailable ? getFileFormatBadge(displayFilename) : null;

              // Only display confidence when explicitly provided as a finite number by the backend
              const rawConfidence = (!isString && typeof ev?.confidence === 'number' && !isNaN(ev.confidence))
                ? ev.confidence
                : (typeof modalConfidence === 'number' && !isNaN(modalConfidence) ? modalConfidence : null);

              const chunkId = !isString && typeof ev?.chunk_id === 'string' ? ev.chunk_id : null;
              const activityId = !isString ? (ev?.activity_id || ev?.id) : null;
              const reason = !isString ? ev?.reason : null;

              // Preserve verbatim snippet text exactly as supplied
              let snippetText = '';
              if (isString) {
                snippetText = ev;
              } else if (ev && typeof ev === 'object') {
                if (typeof ev.snippet === 'string' && ev.snippet.trim()) {
                  snippetText = ev.snippet;
                } else if (typeof ev.text === 'string' && ev.text.trim()) {
                  snippetText = ev.text;
                } else if (typeof ev.description === 'string' && ev.description.trim()) {
                  snippetText = ev.description;
                } else if (typeof ev.reason === 'string' && ev.reason.trim()) {
                  snippetText = `Reason: ${ev.reason}`;
                } else {
                  snippetText = JSON.stringify(ev, null, 2);
                }
              }

              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/70 hover:bg-slate-50 transition-colors space-y-2"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      {isAvailable ? (
                        <div className="flex items-center gap-1.5 font-medium text-indigo-700">
                          <FileText className="w-3.5 h-3.5 shrink-0" />
                          <span className="font-mono text-xs">{displayFilename}</span>
                          {formatBadge && (
                            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border uppercase tracking-wider ${formatBadge.color}`}>
                              {formatBadge.ext}
                            </span>
                          )}
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 font-normal text-slate-400 italic">
                          <FileQuestion className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                          <span>Source filename unavailable</span>
                        </div>
                      )}

                      {activityId && (
                        <span className="font-mono text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded font-bold">
                          {activityId}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-slate-500">
                      {rawConfidence !== null && rawConfidence !== undefined && (
                        <Badge variant="primary" size="sm">
                          Confidence: {(rawConfidence > 1 ? rawConfidence : rawConfidence * 100).toFixed(0)}%
                        </Badge>
                      )}
                      {chunkId && (
                        <span className="font-mono text-slate-400 text-[10px]">
                          ID: {chunkId.slice(0, 8)}...
                        </span>
                      )}
                    </div>
                  </div>

                  {reason && ev?.snippet && (
                    <p className="text-[11px] text-slate-600 font-medium">
                      <span className="text-slate-500 font-semibold">Reason: </span>{reason}
                    </p>
                  )}

                  <div className="bg-white p-3.5 rounded-lg border border-slate-200 text-xs text-slate-700 font-mono whitespace-pre-wrap leading-relaxed shadow-2xs">
                    {snippetText}
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
