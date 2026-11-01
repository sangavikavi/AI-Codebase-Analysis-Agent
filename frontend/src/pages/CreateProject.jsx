import React, { useState } from 'react';
import { Upload, GitBranch, FolderArchive, ArrowRight, ShieldCheck, Sparkles, Layers, Sliders } from 'lucide-react';
import { api } from '../api/client';

export default function CreateProject({ onProjectCreated }) {
  const [sourceType, setSourceType] = useState('zip'); // 'zip' or 'github'
  const [name, setName] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [file, setFile] = useState(null);
  const [personas, setPersonas] = useState(['sde', 'pm']);
  const [depth, setDepth] = useState('Standard');
  const [includeOwasp, setIncludeOwasp] = useState(true);
  const [includeDiagrams, setIncludeDiagrams] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const togglePersona = (p) => {
    if (personas.includes(p)) {
      if (personas.length > 1) {
        setPersonas(personas.filter((x) => x !== p));
      }
    } else {
      setPersonas([...personas, p]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Please provide a project name.');
      return;
    }

    setLoading(true);
    const config = {
      depth,
      verbosity: 'Medium',
      feature_toggles: {
        include_owasp: includeOwasp,
        include_diagrams: includeDiagrams,
      },
      diagram_preferences: ['architecture', 'flowchart', 'sequence', 'er'],
    };

    try {
      let result;
      if (sourceType === 'zip') {
        if (!file) {
          throw new Error('Please select a valid ZIP archive of your codebase.');
        }
        const formData = new FormData();
        formData.append('name', name.trim());
        formData.append('personas', JSON.stringify(personas));
        formData.append('config', JSON.stringify(config));
        formData.append('file', file);
        result = await api.uploadProjectZip(formData);
      } else {
        if (!githubUrl.trim()) {
          throw new Error('Please enter a public GitHub repository URL.');
        }
        result = await api.createProjectGitHub({
          name: name.trim(),
          github_url: githubUrl.trim(),
          personas,
          config,
        });
      }

      // Trigger multi-agent pipeline start
      await api.startAnalysis(result.project_id);

      onProjectCreated({
        id: result.project_id,
        name: name.trim(),
      });
    } catch (err) {
      setError(err.message || 'Error creating project.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white tracking-tight">Create & Analyze Project</h2>
        <p className="text-sm text-slate-400 mt-1">
          Provide your source codebase to launch autonomous multi-agent analysis and persona report generation.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Ingestion Source Switcher */}
        <div className="glass-panel rounded-2xl p-6">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Codebase Source
          </label>
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setSourceType('zip')}
              className={`p-4 rounded-xl border flex items-center gap-3 transition text-left cursor-pointer ${
                sourceType === 'zip'
                  ? 'bg-blue-600/15 border-blue-500 text-white'
                  : 'bg-slate-900/50 border-white/5 text-slate-400 hover:border-white/10'
              }`}
            >
              <FolderArchive className={`w-5 h-5 ${sourceType === 'zip' ? 'text-blue-400' : 'text-slate-400'}`} />
              <div>
                <div className="font-semibold text-sm">ZIP Archive</div>
                <div className="text-xs text-slate-400">Upload codebase file up to 100MB</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setSourceType('github')}
              className={`p-4 rounded-xl border flex items-center gap-3 transition text-left cursor-pointer ${
                sourceType === 'github'
                  ? 'bg-blue-600/15 border-blue-500 text-white'
                  : 'bg-slate-900/50 border-white/5 text-slate-400 hover:border-white/10'
              }`}
            >
              <GitBranch className={`w-5 h-5 ${sourceType === 'github' ? 'text-blue-400' : 'text-slate-400'}`} />
              <div>
                <div className="font-semibold text-sm">Public GitHub URL</div>
                <div className="text-xs text-slate-400">Clone public repository</div>
              </div>
            </button>
          </div>

          <div className="mt-6 space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Project Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Acme Billing Engine"
                className="w-full px-4 py-2.5 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
              />
            </div>

            {sourceType === 'zip' ? (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Upload Codebase (.zip)</label>
                <div className="relative border-2 border-dashed border-white/10 hover:border-blue-500/50 rounded-xl p-8 text-center transition bg-slate-900/30">
                  <input
                    type="file"
                    accept=".zip"
                    onChange={(e) => setFile(e.target.files[0] || null)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-200">
                    {file ? file.name : 'Click or drag ZIP archive here'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">Maximum 100MB • Only .zip format</p>
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">GitHub Repository URL</label>
                <input
                  type="url"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/owner/repository"
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-900/80 border border-white/10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
                />
              </div>
            )}
          </div>
        </div>

        {/* Personas & Agent Config */}
        <div className="glass-panel rounded-2xl p-6">
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Target Documentation Personas
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            <div
              onClick={() => togglePersona('sde')}
              className={`p-4 rounded-xl border cursor-pointer transition ${
                personas.includes('sde')
                  ? 'bg-blue-600/15 border-blue-500 text-white'
                  : 'bg-slate-900/50 border-white/5 text-slate-400'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-sm">SDE Technical Persona</span>
                <span className="text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-400">Engineering</span>
              </div>
              <p className="text-xs text-slate-400">
                System topology, API schemas, DB relational models, deployment guide, and OWASP security benchmarks.
              </p>
            </div>

            <div
              onClick={() => togglePersona('pm')}
              className={`p-4 rounded-xl border cursor-pointer transition ${
                personas.includes('pm')
                  ? 'bg-purple-600/15 border-purple-500 text-white'
                  : 'bg-slate-900/50 border-white/5 text-slate-400'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold text-sm">PM Business Persona</span>
                <span className="text-xs px-2 py-0.5 rounded bg-purple-500/20 text-purple-400">Product</span>
              </div>
              <p className="text-xs text-slate-400">
                Feature inventory, end-to-end customer journeys, priority matrix, external integrations, and strategic roadmap.
              </p>
            </div>
          </div>

          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Analysis Depth & Features
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
            {['Quick', 'Standard', 'Deep'].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDepth(d)}
                className={`py-2 px-3 rounded-xl border text-xs font-medium transition cursor-pointer ${
                  depth === d
                    ? 'bg-blue-600 text-white border-blue-500 shadow-md'
                    : 'bg-slate-900 border-white/5 text-slate-400 hover:text-white'
                }`}
              >
                {d} Analysis
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-4 border-t border-white/5 text-xs">
            <label className="flex items-center gap-2 cursor-pointer text-slate-300">
              <input
                type="checkbox"
                checked={includeOwasp}
                onChange={(e) => setIncludeOwasp(e.target.checked)}
                className="rounded border-white/10 bg-slate-900 text-blue-600"
              />
              <span>Live OWASP & Framework Web Research</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-slate-300">
              <input
                type="checkbox"
                checked={includeDiagrams}
                onChange={(e) => setIncludeDiagrams(e.target.checked)}
                className="rounded border-white/10 bg-slate-900 text-blue-600"
              />
              <span>Synthesize 4 Mermaid System Diagrams</span>
            </label>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-xl shadow-blue-600/30 transition disabled:opacity-50 cursor-pointer"
        >
          {loading ? (
            'Ingesting & Launching Multi-Agent Pipeline...'
          ) : (
            <>
              <span>Launch Multi-Agent Analysis</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}
