import React, { useEffect, useState } from 'react';
import { 
  Users, 
  FolderKanban, 
  Activity, 
  Percent, 
  ShieldCheck, 
  Trash2, 
  Search, 
  AlertTriangle, 
  Cpu 
} from 'lucide-react';
import { api } from '../api/client';

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [traces, setTraces] = useState([]);
  const [errorLogs, setErrorLogs] = useState([]);
  const [activeTab, setActiveTab] = useState('users'); // 'users', 'projects', 'traces', 'errors'
  const [loading, setLoading] = useState(true);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [an, uList, pList, trData, errs] = await Promise.all([
        api.getAdminAnalytics(),
        api.getAdminUsers(),
        api.getAdminProjects(),
        api.getAdminTraces(),
        api.getAdminErrorLogs(),
      ]);
      setAnalytics(an);
      setUsers(uList);
      setProjects(pList);
      setTraces(trData.traces || []);
      setErrorLogs(errs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const handleDeleteUser = async (id) => {
    if (!confirm(`Delete user #${id} and all their projects?`)) return;
    try {
      await api.deleteAdminUser(id);
      setUsers(users.filter((u) => u.id !== id));
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteProject = async (id) => {
    if (!confirm(`Delete project ${id}?`)) return;
    try {
      await api.deleteAdminProject(id);
      setProjects(projects.filter((p) => p.id !== id));
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <ShieldCheck className="w-6 h-6 text-blue-400" />
          <span>Admin & Observability Console</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          System analytics, user management, project governance, and Langfuse LLM trace trees.
        </p>
      </div>

      {/* Analytics Metric Cards */}
      {analytics && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Total Users</span>
              <Users className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-3xl font-extrabold text-white">{analytics.total_users}</div>
          </div>

          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Total Projects</span>
              <FolderKanban className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-3xl font-extrabold text-white">{analytics.total_projects}</div>
          </div>

          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Active Analyses</span>
              <Activity className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-3xl font-extrabold text-white">{analytics.active_analyses}</div>
          </div>

          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center justify-between text-slate-400 text-xs font-semibold uppercase tracking-wider mb-2">
              <span>Completion Rate</span>
              <Percent className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-3xl font-extrabold text-white">{analytics.completion_rate_percent.toFixed(1)}%</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex rounded-xl bg-slate-900/60 p-1 mb-6 border border-white/5 max-w-xl">
        {[
          { id: 'users', label: `Users (${users.length})` },
          { id: 'projects', label: `Projects (${projects.length})` },
          { id: 'traces', label: `Langfuse Traces (${traces.length})` },
          { id: 'errors', label: `Error Logs (${errorLogs.length})` },
        ].map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition cursor-pointer ${
              activeTab === t.id ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      {loading ? (
        <div className="py-20 text-center text-slate-400">Loading admin data...</div>
      ) : activeTab === 'users' ? (
        <div className="glass-panel rounded-2xl overflow-hidden border border-white/10">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono border-b border-white/10">
              <tr>
                <th className="p-4">ID</th>
                <th className="p-4">Email</th>
                <th className="p-4">Role</th>
                <th className="p-4">Projects</th>
                <th className="p-4">Joined</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 font-mono text-slate-400">#{u.id}</td>
                  <td className="p-4 font-medium text-white">{u.email}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded uppercase font-mono text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {u.role}
                    </span>
                  </td>
                  <td className="p-4 font-mono">{u.project_count}</td>
                  <td className="p-4 text-slate-400">{u.created_at ? u.created_at.slice(0, 10) : ''}</td>
                  <td className="p-4 text-right">
                    {u.id !== 1 && (
                      <button
                        onClick={() => handleDeleteUser(u.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : activeTab === 'projects' ? (
        <div className="glass-panel rounded-2xl overflow-hidden border border-white/10">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono border-b border-white/10">
              <tr>
                <th className="p-4">Project</th>
                <th className="p-4">Stack</th>
                <th className="p-4">Status</th>
                <th className="p-4">Files / Routes</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {projects.map((p) => (
                <tr key={p.id} className="hover:bg-slate-800/30 transition">
                  <td className="p-4 font-medium text-white">{p.name}</td>
                  <td className="p-4 text-slate-400 font-mono text-[11px]">{p.detected_stack || 'N/A'}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded uppercase font-mono text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {p.status}
                    </span>
                  </td>
                  <td className="p-4 font-mono">{p.total_files} / {p.endpoint_count}</td>
                  <td className="p-4 text-right">
                    <button
                      onClick={() => handleDeleteProject(p.id)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : activeTab === 'traces' ? (
        <div className="space-y-3">
          {traces.length === 0 ? (
            <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 text-sm">
              No Langfuse execution traces recorded yet.
            </div>
          ) : (
            traces.map((tr) => (
              <div key={tr.id} className="glass-card rounded-xl p-4 flex flex-col gap-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-blue-400 flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5" />
                    <span>Agent: {tr.agent_name}</span>
                  </span>
                  <span className="font-mono text-slate-400 text-[11px]">
                    Tokens: <strong className="text-white">{tr.tokens}</strong> • 
                    Latency: <strong className="text-amber-400">{tr.latency_sec}s</strong> • 
                    Cost: <strong className="text-emerald-400">${tr.cost_usd}</strong>
                  </span>
                </div>
                <div className="text-[11px] text-slate-300 font-mono bg-black/30 p-2.5 rounded-lg border border-white/5 line-clamp-2">
                  Prompt: {tr.prompt_snippet}
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {errorLogs.length === 0 ? (
            <div className="glass-panel rounded-2xl p-12 text-center text-slate-400 text-sm">
              Clean state: Zero errors recorded in event logs.
            </div>
          ) : (
            errorLogs.map((er) => (
              <div key={er.id} className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-300 flex items-start gap-3">
                <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold mb-1">[{er.stage}] — {er.timestamp}</div>
                  <p>{er.message}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
