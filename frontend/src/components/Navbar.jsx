import React from 'react';
import { Bot, LogOut, Shield, FolderGit2 } from 'lucide-react';
import { getUserInfo } from '../api/client';

export default function Navbar({ activeProject, onLogout }) {
  const user = getUserInfo();

  return (
    <header className="h-16 border-b border-white/10 bg-[#0c1220]/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Bot className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-base bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
            Multi-Agent Codebase Analysis
          </h1>
          <p className="text-xs text-slate-400">Autonomous SDE & PM Documentation</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {activeProject && (
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-xs">
            <FolderGit2 className="w-4 h-4 text-blue-400" />
            <span className="text-slate-400">Active:</span>
            <span className="font-semibold text-blue-300">{activeProject.name}</span>
          </div>
        )}

        {user && (
          <div className="flex items-center gap-3 pl-2 border-l border-white/10">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-medium text-slate-200">{user.email}</div>
              <div className="text-[10px] uppercase font-mono font-bold tracking-wider text-blue-400">
                {user.role}
              </div>
            </div>
            <button
              onClick={onLogout}
              title="Sign Out"
              className="p-2 rounded-lg bg-slate-800/80 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-white/5 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
