import React, { useState } from 'react';
import { Search, Zap, Code2, Briefcase, FileCode, CheckCircle2, Clock } from 'lucide-react';
import { api } from '../api/client';

export default function CodebaseQA({ activeProject }) {
  const [question, setQuestion] = useState('');
  const [persona, setPersona] = useState('sde');
  const [loading, setLoading] = useState(false);
  const [qaResult, setQaResult] = useState(null);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!question.trim() || !activeProject?.id) return;

    setError('');
    setLoading(true);
    setQaResult(null);

    try {
      const res = await api.askQA(activeProject.id, question.trim(), persona);
      setQaResult(res);
    } catch (err) {
      setError(err.message || 'Error executing Q&A query.');
    } finally {
      setLoading(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="p-8 text-center text-slate-400">
        No active project selected. Select a project from the dashboard.
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white tracking-tight">Codebase RAG Q&A</h2>
        <p className="text-sm text-slate-400 mt-1">
          Ask queries over indexed source code chunks. All answers cite verified line ranges and respond in under 3 seconds.
        </p>
      </div>

      {/* Query Form */}
      <div className="glass-panel rounded-2xl p-6 mb-8">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Answer Style:</span>
            <div className="flex rounded-lg bg-slate-900 p-1 border border-white/5">
              <button
                type="button"
                onClick={() => setPersona('sde')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition cursor-pointer ${
                  persona === 'sde' ? 'bg-blue-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                <span>SDE (Technical)</span>
              </button>
              <button
                type="button"
                onClick={() => setPersona('pm')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition cursor-pointer ${
                  persona === 'pm' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Briefcase className="w-3.5 h-3.5" />
                <span>PM (Business Value)</span>
              </button>
            </div>
          </div>

          <div className="relative">
            <input
              type="text"
              required
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g. How is user authentication implemented?"
              className="w-full pl-11 pr-32 py-3.5 rounded-xl bg-slate-900/90 border border-white/10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition shadow-inner"
            />
            <Search className="w-5 h-5 text-slate-500 absolute left-4 top-3.5" />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="absolute right-2 top-2 px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs flex items-center gap-2 transition disabled:opacity-50 cursor-pointer shadow-md"
            >
              {loading ? (
                <span>Searching...</span>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5" />
                  <span>Answer</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Answer Container */}
      {qaResult && (
        <div className="glass-panel rounded-2xl p-6 border-blue-500/20 shadow-2xl">
          <div className="flex items-center justify-between border-b border-white/5 pb-3 mb-4">
            <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Grounded Answer ({qaResult.persona.toUpperCase()})</span>
            </span>
            <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>Latency: <strong className="text-slate-200">{qaResult.response_time_ms.toFixed(1)}ms</strong> (&lt;3s SLA)</span>
            </div>
          </div>

          <p className="text-sm text-slate-200 leading-relaxed mb-6 font-normal">
            {qaResult.answer}
          </p>

          {/* Code Citations */}
          {qaResult.citations && qaResult.citations.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <FileCode className="w-4 h-4 text-purple-400" />
                <span>Verified Code Citations ({qaResult.citations.length})</span>
              </h4>
              <div className="space-y-3">
                {qaResult.citations.map((cit, idx) => (
                  <div key={idx} className="p-4 rounded-xl bg-slate-900/80 border border-white/5">
                    <div className="flex items-center justify-between text-xs mb-2">
                      <span className="font-mono text-blue-300 font-semibold">{cit.file_path}</span>
                      <span className="text-slate-500 font-mono">Lines {cit.start_line} - {cit.end_line}</span>
                    </div>
                    <pre className="p-3 rounded-lg bg-black/40 font-mono text-xs text-slate-300 overflow-x-auto border border-white/5">
                      {cit.snippet}
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
