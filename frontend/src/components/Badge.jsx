import React from 'react';

export default function Badge({ children, variant = 'default', size = 'md' }) {
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5',
  };

  const variantMap = {
    // Severity / Health
    Critical: 'bg-rose-100 text-rose-800 border-rose-200 font-semibold',
    critical: 'bg-rose-100 text-rose-800 border-rose-200 font-semibold',
    High: 'bg-orange-100 text-orange-800 border-orange-200 font-medium',
    high: 'bg-orange-100 text-orange-800 border-orange-200 font-medium',
    Medium: 'bg-amber-100 text-amber-800 border-amber-200 font-medium',
    medium: 'bg-amber-100 text-amber-800 border-amber-200 font-medium',
    Low: 'bg-blue-100 text-blue-800 border-blue-200',
    low: 'bg-blue-100 text-blue-800 border-blue-200',
    Healthy: 'bg-emerald-100 text-emerald-800 border-emerald-200 font-semibold',
    healthy: 'bg-emerald-100 text-emerald-800 border-emerald-200 font-semibold',
    'Needs Attention': 'bg-amber-100 text-amber-800 border-amber-200 font-medium',
    'needs attention': 'bg-amber-100 text-amber-800 border-amber-200 font-medium',
    'At Risk': 'bg-orange-100 text-orange-800 border-orange-200 font-semibold',
    'at risk': 'bg-orange-100 text-orange-800 border-orange-200 font-semibold',

    // Status
    completed: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    Completed: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    in_progress: 'bg-sky-100 text-sky-800 border-sky-200',
    'In progress': 'bg-sky-100 text-sky-800 border-sky-200',
    pending: 'bg-amber-50 text-amber-700 border-amber-200',
    Pending: 'bg-amber-50 text-amber-700 border-amber-200',
    active: 'bg-rose-100 text-rose-800 border-rose-200',
    unresolved: 'bg-rose-100 text-rose-800 border-rose-200',
    delayed: 'bg-rose-100 text-rose-800 border-rose-200',

    // Formats & Tech
    pdf: 'bg-red-50 text-red-700 border-red-200 font-mono',
    PDF: 'bg-red-50 text-red-700 border-red-200 font-mono',
    docx: 'bg-blue-50 text-blue-700 border-blue-200 font-mono',
    DOCX: 'bg-blue-50 text-blue-700 border-blue-200 font-mono',
    csv: 'bg-emerald-50 text-emerald-700 border-emerald-200 font-mono',
    CSV: 'bg-emerald-50 text-emerald-700 border-emerald-200 font-mono',
    txt: 'bg-slate-100 text-slate-700 border-slate-200 font-mono',
    TXT: 'bg-slate-100 text-slate-700 border-slate-200 font-mono',

    // Generic
    primary: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    secondary: 'bg-slate-100 text-slate-700 border-slate-200',
    success: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    warning: 'bg-amber-100 text-amber-800 border-amber-200',
    danger: 'bg-rose-100 text-rose-800 border-rose-200',
    info: 'bg-cyan-100 text-cyan-800 border-cyan-200',
    default: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  const styleClass = variantMap[variant] || variantMap.default;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border ${sizeClasses[size] || sizeClasses.md} ${styleClass} whitespace-nowrap`}
    >
      {children}
    </span>
  );
}
