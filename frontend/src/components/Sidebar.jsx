import React from 'react';
import {
  LayoutDashboard,
  UploadCloud,
  Database,
  Target,
  AlertTriangle,
  ShieldAlert,
  Cpu,
  Layers,
  Sparkles,
} from 'lucide-react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  onSelectTab,
  onNavigate,
}) {
  const handleTabClick = (id) => {
    if (typeof onSelectTab === 'function') {
      onSelectTab(id);
    } else if (typeof setActiveTab === 'function') {
      setActiveTab(id);
    } else if (typeof onNavigate === 'function') {
      onNavigate(id);
    }
  };

  const navSections = [
    {
      title: 'Executive Intelligence',
      items: [
        { id: 'overview', label: 'Overview Dashboard', icon: LayoutDashboard },
        { id: 'orchestrator', label: 'Multi-Agent Analysis', icon: Cpu, badge: 'Unified' },
      ],
    },
    {
      title: 'Milestone 1 — Data & RAG',
      items: [
        { id: 'upload', label: 'Document Ingestion', icon: UploadCloud },
        { id: 'rag', label: 'RAG Knowledge Base', icon: Database },
      ],
    },
    {
      title: 'Milestone 2 — Autonomous Agents',
      items: [
        { id: 'scope', label: 'Scope & Deliverables', icon: Target },
        { id: 'risks', label: 'Risk & Forecasting', icon: AlertTriangle },
        { id: 'blockers', label: 'Blockers & Action Items', icon: ShieldAlert },
      ],
    },
    {
      title: 'Internship Governance',
      items: [
        { id: 'architecture', label: 'Architecture & Design', icon: Layers },
      ],
    },
  ];

  return (
    <aside className="w-68 bg-white border-r border-slate-200/80 flex flex-col shrink-0 h-screen sticky top-0">
      {/* Brand Logo & Name */}
      <div 
        onClick={() => handleTabClick('overview')}
        className="p-5 border-b border-slate-100 flex items-center gap-3 cursor-pointer hover:bg-slate-50/50 transition-colors"
      >
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-500 flex items-center justify-center text-white shadow-md shadow-indigo-100 shrink-0">
          <Sparkles className="w-5 h-5" />
        </div>
        <div className="overflow-hidden">
          <h2 className="text-sm font-bold text-slate-800 leading-tight truncate">
            Project Intelligence
          </h2>
          <span className="text-[11px] font-medium text-indigo-600 block truncate">
            Risk Advisor Platform
          </span>
        </div>
      </div>

      {/* Navigation Sections */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navSections.map((sec, sIdx) => (
          <div key={sIdx}>
            <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
              {sec.title}
            </p>
            <div className="space-y-0.5">
              {sec.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleTabClick(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-2xs border-l-2 border-indigo-600'
                        : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <Icon
                        className={`w-4 h-4 shrink-0 ${
                          isActive ? 'text-indigo-600' : 'text-slate-400'
                        }`}
                      />
                      <span className="truncate">{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={`text-[10px] px-1.5 py-0.5 rounded-md font-semibold ${
                          isActive
                            ? 'bg-indigo-200/60 text-indigo-800'
                            : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer Info Box */}
      <div className="p-3 m-3 bg-slate-50 border border-slate-200/80 rounded-xl">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700 mb-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>Infosys Springboard</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-snug">
          Milestone 1 & Milestone 2 Complete. 102/102 automated tests verified.
        </p>
      </div>
    </aside>
  );
}
