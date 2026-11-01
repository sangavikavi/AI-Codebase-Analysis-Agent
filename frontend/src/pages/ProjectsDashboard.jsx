import React, { useEffect, useState } from 'react';
import { FolderGit2, Trash2, ArrowUpRight, Plus, RefreshCw, Cpu, Layers } from 'lucide-react';
import { api } from '../api/client';

export default function ProjectsDashboard({ onSelectProject, onNavigateToCreate }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const data = await api.listProjects();
      setProjects(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this project?')) return;
    setDeletingId(id);
    try {
      await api.deleteProject(id);
      setProjects(projects.filter((p) => p.id !== id));
    } catch (err) {
      alert(err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'analyzing':
      case 'preprocessing':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30 animate-pulse';
      case 'paused':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Projects Dashboard</h2>
          <p className="text-sm text-slate-400 mt-1">
            Browse and manage software repositories analyzed by the multi-agent team.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadProjects}
            className="p-2.5 rounded-xl bg-slate-900 border border-white/10 hover:bg-slate-800 text-slate-300 transition"
            title="Refresh list"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={onNavigateToCreate}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition shadow-lg shadow-blue-600/25"
          >
            <Plus className="w-4 h-4" />
            <span>New Analysis</span>
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24 text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mr-3 text-blue-400" />
          <span>Loading project catalog...</span>
        </div>
      ) : projects.length === 0 ? (
        <div className="glass-panel rounded-2xl p-12 text-center max-w-md mx-auto">
          <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mx-auto mb-4">
            <FolderGit2 className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">No projects yet</h3>
          <p className="text-sm text-slate-400 mb-6">
            Upload any codebase ZIP file or connect a public GitHub repository to start multi-agent analysis.
          </p>
          <button
            onClick={onNavigateToCreate}
            className="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition"
          >
            Analyze First Repository
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div
              key={proj.id}
              onClick={() => onSelectProject(proj)}
              className="glass-card rounded-2xl p-6 cursor-pointer flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between gap-3 mb-3">
                  <span className={`text-[11px] font-semibold uppercase px-2.5 py-1 rounded-full border ${getStatusBadge(proj.status)}`}>
                    {proj.status}
                  </span>
                  <button
                    onClick={(e) => handleDelete(e, proj.id)}
                    disabled={deletingId === proj.id}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition"
                    title="Delete project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <h3 className="text-lg font-bold text-white group-hover:text-blue-400 transition mb-1">
                  {proj.name}
                </h3>

                <p className="text-xs text-slate-400 mb-4 line-clamp-1">
                  Stack: <span className="text-slate-300 font-medium">{proj.detected_stack || 'Detecting...'}</span>
                </p>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>{proj.current_stage || 'Progress'}</span>
                    <span className="font-semibold text-slate-300">{proj.progress_percentage?.toFixed(0)}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(100, Math.max(0, proj.progress_percentage || 0))}%` }}
                    />
                  </div>
                </div>
              </div>

              <div>
                <div className="grid grid-cols-2 gap-2 pt-3 border-t border-white/5 text-xs text-slate-400 mb-4">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-slate-500" />
                    <span>{proj.total_files || 0} files</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-slate-500" />
                    <span>{proj.endpoint_count || 0} routes</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs font-medium text-blue-400 group-hover:text-blue-300">
                  <span>Open Analysis Workspace</span>
                  <ArrowUpRight className="w-4 h-4 transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
