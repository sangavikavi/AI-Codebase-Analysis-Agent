import React, { useEffect, useState } from 'react';
import { 
  FileDown, 
  FileText, 
  Code2, 
  Briefcase, 
  Layers, 
  ExternalLink, 
  Check, 
  Download 
} from 'lucide-react';
import { api, getAuthToken } from '../api/client';
import MermaidViewer from '../components/MermaidViewer';

export default function DocumentationView({ activeProject }) {
  const [activePersonaTab, setActivePersonaTab] = useState('sde'); // 'sde', 'pm', 'diagrams'
  const [sdeReport, setSdeReport] = useState(null);
  const [pmReport, setPmReport] = useState(null);
  const [diagrams, setDiagrams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      if (!activeProject?.id) return;
      setLoading(true);
      try {
        const reps = await api.getReports(activeProject.id);
        const sde = reps.find((r) => r.persona === 'sde');
        const pm = reps.find((r) => r.persona === 'pm');
        const diag = reps.find((r) => r.persona === 'diagrams');

        if (sde) setSdeReport(sde);
        if (pm) setPmReport(pm);
        if (diag) setDiagrams(diag.diagrams_json || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [activeProject?.id]);

  const handleDownload = async (format) => {
    if (!activeProject?.id) return;
    const url = format === 'markdown' 
      ? api.getExportMarkdownUrl(activeProject.id) 
      : api.getExportPdfUrl(activeProject.id);

    try {
      const token = getAuthToken();
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `${activeProject.name}_documentation.${format === 'markdown' ? 'md' : 'pdf'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert(err.message);
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
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header and Exports Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Role-Specific Documentation</h2>
          <p className="text-sm text-slate-400 mt-1">
            Engineered documentation tailored to SDE technical depth and PM business clarity.
          </p>
        </div>

        {/* Prominent Export Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => handleDownload('markdown')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-white/10 text-white font-medium text-xs transition shadow-md cursor-pointer"
          >
            <FileText className="w-4 h-4 text-blue-400" />
            <span>Export Markdown (.md)</span>
          </button>

          <button
            onClick={() => handleDownload('pdf')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs transition shadow-lg shadow-blue-500/25 cursor-pointer"
          >
            <FileDown className="w-4 h-4" />
            <span>Export PDF (.pdf)</span>
          </button>
        </div>
      </div>

      {/* Persona Tab Switcher */}
      <div className="flex rounded-2xl bg-slate-900/60 p-1.5 mb-8 border border-white/5 max-w-lg">
        <button
          onClick={() => setActivePersonaTab('sde')}
          className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition cursor-pointer ${
            activePersonaTab === 'sde'
              ? 'bg-blue-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Code2 className="w-4 h-4" />
          <span>SDE Technical Specs</span>
        </button>

        <button
          onClick={() => setActivePersonaTab('pm')}
          className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition cursor-pointer ${
            activePersonaTab === 'pm'
              ? 'bg-purple-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Briefcase className="w-4 h-4" />
          <span>PM Business Architecture</span>
        </button>

        <button
          onClick={() => setActivePersonaTab('diagrams')}
          className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition cursor-pointer ${
            activePersonaTab === 'diagrams'
              ? 'bg-emerald-600 text-white shadow-md'
              : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Mermaid Diagrams</span>
        </button>
      </div>

      {loading ? (
        <div className="text-center py-20 text-slate-400">Loading persona specifications...</div>
      ) : activePersonaTab === 'sde' ? (
        <div className="glass-panel rounded-2xl p-8">
          {sdeReport ? (
            <div className="prose prose-invert max-w-none prose-headings:text-slate-100 prose-p:text-slate-300 prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/10 prose-table:border-white/10">
              <div dangerouslySetInnerHTML={{ __html: renderMarkdown(sdeReport.content_markdown) }} />
            </div>
          ) : (
            <div className="text-center py-16 text-slate-400">
              SDE report has not been generated yet. Please run the analysis first.
            </div>
          )}
        </div>
      ) : activePersonaTab === 'pm' ? (
        <div className="glass-panel rounded-2xl p-8">
          {pmReport ? (
            <div className="prose prose-invert max-w-none prose-headings:text-slate-100 prose-p:text-slate-300 prose-pre:bg-black/40 prose-pre:border prose-pre:border-white/10">
              <div dangerouslySetInnerHTML={{ __html: renderMarkdown(pmReport.content_markdown) }} />
            </div>
          ) : (
            <div className="text-center py-16 text-slate-400">
              PM report has not been generated yet. Please run the analysis first.
            </div>
          )}
        </div>
      ) : (
        <div>
          {diagrams.length > 0 ? (
            diagrams.map((d, idx) => (
              <MermaidViewer
                key={idx}
                title={d.title}
                type={d.type}
                code={d.code}
              />
            ))
          ) : (
            <div className="glass-panel rounded-2xl p-12 text-center text-slate-400">
              No diagrams generated yet for this project.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Lightweight Markdown parser for rendering headings, lists, tables, code blocks and links
function renderMarkdown(md) {
  if (!md) return '';
  let html = md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks
  html = html.replace(/```([\s\S]*?)```/g, (match, p1) => {
    return `<pre class="bg-black/50 p-4 rounded-xl font-mono text-xs text-blue-300 overflow-x-auto my-3 border border-white/5"><code>${p1}</code></pre>`;
  });

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h3 class="text-base font-bold text-blue-400 mt-6 mb-2">$1</h3>');
  html = html.replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold text-white border-b border-white/10 pb-2 mt-8 mb-3">$1</h2>');
  html = html.replace(/^# (.*$)/gim, '<h1 class="text-2xl font-extrabold text-white mb-4">$1</h1>');

  // Bold & Italic
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em class="text-slate-400">$1</em>');

  // Inline Code
  html = html.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-slate-800 text-blue-300 font-mono text-xs">$1</code>');

  // Bullet Lists
  html = html.replace(/^\- (.*$)/gim, '<li class="ml-4 list-disc text-slate-300 my-1">$1</li>');

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-400 underline hover:text-blue-300">$1</a>');

  // Paragraphs
  html = html.replace(/\n\n/g, '<br/><br/>');

  return html;
}
