import React from 'react';

export default function StatCard({
  title,
  value,
  subtext,
  icon: Icon,
  trend,
  color = 'indigo',
  onClick,
}) {
  const colorStyles = {
    indigo: {
      bg: 'bg-indigo-50/70',
      text: 'text-indigo-600',
      border: 'hover:border-indigo-300',
      glow: 'group-hover:bg-indigo-500',
    },
    emerald: {
      bg: 'bg-emerald-50/70',
      text: 'text-emerald-600',
      border: 'hover:border-emerald-300',
      glow: 'group-hover:bg-emerald-500',
    },
    amber: {
      bg: 'bg-amber-50/70',
      text: 'text-amber-600',
      border: 'hover:border-amber-300',
      glow: 'group-hover:bg-amber-500',
    },
    rose: {
      bg: 'bg-rose-50/70',
      text: 'text-rose-600',
      border: 'hover:border-rose-300',
      glow: 'group-hover:bg-rose-500',
    },
    purple: {
      bg: 'bg-purple-50/70',
      text: 'text-purple-600',
      border: 'hover:border-purple-300',
      glow: 'group-hover:bg-purple-500',
    },
    blue: {
      bg: 'bg-sky-50/70',
      text: 'text-sky-600',
      border: 'hover:border-sky-300',
      glow: 'group-hover:bg-sky-500',
    },
  };

  const c = colorStyles[color] || colorStyles.indigo;

  return (
    <div
      onClick={onClick}
      className={`group relative bg-white border border-slate-200/80 rounded-2xl p-5 shadow-xs transition-all duration-200 hover:shadow-md ${
        onClick ? 'cursor-pointer ' + c.border : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </p>
          <h3 className="text-2xl font-bold text-slate-800 mt-1 tracking-tight">
            {value}
          </h3>
          {subtext && (
            <p className="text-xs text-slate-500 mt-1 line-clamp-1">{subtext}</p>
          )}
        </div>
        {Icon && (
          <div
            className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${c.bg} ${c.text} transition-transform group-hover:scale-105`}
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center text-xs text-slate-500">
          {trend}
        </div>
      )}
    </div>
  );
}
