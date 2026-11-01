import React from 'react';
import { 
  FolderKanban, 
  PlusCircle, 
  Activity, 
  FileText, 
  MessageSquareCode, 
  ShieldAlert 
} from 'lucide-react';
import { getUserInfo } from '../api/client';

export default function Sidebar({ activeTab, setActiveTab }) {
  const user = getUserInfo();

  const navItems = [
    { id: 'projects', label: 'Projects Dashboard', icon: FolderKanban },
    { id: 'create', label: 'Create Project', icon: PlusCircle },
    { id: 'analysis', label: 'Live Analysis & Steering', icon: Activity },
    { id: 'docs', label: 'Documentation & Reports', icon: FileText },
    { id: 'qa', label: 'Codebase RAG Q&A', icon: MessageSquareCode },
  ];

  if (user?.role === 'admin') {
    navItems.push({ id: 'admin', label: 'Admin & Observability', icon: ShieldAlert });
  }

  return (
    <aside className="w-64 border-r border-white/10 bg-[#0c1220]/60 backdrop-blur-md p-4 flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-1.5">
        <div className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Workspace
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      <div className="p-3 rounded-xl bg-slate-900/40 border border-white/5 text-xs text-slate-400">
        <p className="font-semibold text-slate-300 mb-1">Multi-Agent Engine</p>
        <p className="leading-relaxed text-[11px]">7 LangGraph agents orchestrating code analysis, web research, and persona reports.</p>
      </div>
    </aside>
  );
}
