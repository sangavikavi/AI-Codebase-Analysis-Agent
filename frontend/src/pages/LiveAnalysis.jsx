import React, { useEffect, useState, useRef } from 'react';
import { 
  Play, 
  Pause, 
  Activity, 
  MessageSquare, 
  Send, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  FileCode, 
  ShieldCheck 
} from 'lucide-react';
import { api } from '../api/client';

export default function LiveAnalysis({ activeProject, onGoToReports }) {
  const [project, setProject] = useState(null);
  const [events, setEvents] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [inputMsg, setInputMsg] = useState('');
  const [sendingChat, setSendingChat] = useState(false);
  const [activeTab, setActiveTab] = useState('feed'); // 'feed' or 'chat'
  const chatEndRef = useRef(null);

  const fetchProjectData = async () => {
    if (!activeProject?.id) return;
    try {
      const p = await api.getProject(activeProject.id);
      setProject(p);
      const evs = await api.getProjectEvents(activeProject.id);
      setEvents(evs);
      const chats = await api.getChatHistory(activeProject.id);
      setChatMessages(chats);
    } catch (err) {
      console.error(err);
    }
  };

  // Poll project & events every 2 seconds while analyzing
  useEffect(() => {
    fetchProjectData();
    const interval = setInterval(() => {
      fetchProjectData();
    }, 2000);

    return () => clearInterval(interval);
  }, [activeProject?.id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const handlePause = async () => {
    try {
      await api.pauseAnalysis(activeProject.id);
      fetchProjectData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleResume = async () => {
    try {
      await api.resumeAnalysis(activeProject.id);
      fetchProjectData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!inputMsg.trim()) return;

    const userText = inputMsg.trim();
    setInputMsg('');
    setSendingChat(true);

    try {
      await api.sendChatMessage(activeProject.id, userText);
      const chats = await api.getChatHistory(activeProject.id);
      setChatMessages(chats);
    } catch (err) {
      alert(err.message);
    } finally {
      setSendingChat(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="p-8 text-center text-slate-400">
        No active project selected. Select a project from the dashboard.
      </div>
    );
  }

  const isCompleted = project?.status === 'completed';
  const isPaused = project?.status === 'paused';

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Top Header Card */}
      <div className="glass-panel rounded-2xl p-6 mb-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-white tracking-tight">{project?.name || activeProject.name}</h2>
              <span className={`text-xs uppercase font-semibold px-2.5 py-0.5 rounded-full border ${
                isCompleted
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : isPaused
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  : 'bg-blue-500/10 text-blue-400 border-blue-500/30 animate-pulse'
              }`}>
                {project?.status}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Stack: <span className="text-slate-300 font-medium">{project?.detected_stack || 'Detecting stack...'}</span> • 
              Stage: <span className="text-blue-400 font-semibold">{project?.current_stage || 'Initializing'}</span>
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            {project?.status === 'analyzing' && (
              <button
                onClick={handlePause}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 font-medium text-xs transition cursor-pointer"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
            )}

            {(isPaused || project?.status === 'created') && (
              <button
                onClick={handleResume}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition cursor-pointer shadow-md shadow-blue-500/25"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Resume</span>
              </button>
            )}

            {isCompleted && (
              <button
                onClick={onGoToReports}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition cursor-pointer shadow-md shadow-emerald-500/25"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>View Reports & Diagrams</span>
              </button>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div>
          <div className="flex justify-between text-xs text-slate-400 mb-1.5">
            <span>Overall Analysis Progress</span>
            <span className="font-bold text-slate-200">{project?.progress_percentage?.toFixed(0) || 0}%</span>
          </div>
          <div className="w-full h-2.5 rounded-full bg-slate-800/80 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, project?.progress_percentage || 0))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Container: Feed & Guarded Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Activity Feed (2 Cols) */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6 flex flex-col h-[580px]">
          <div className="flex items-center justify-between border-b border-white/5 pb-3 mb-4">
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400" />
              <span>Structured Activity Feed</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">{events.length} events</span>
          </div>

          <div className="overflow-y-auto flex-1 space-y-2.5 pr-1">
            {events.length === 0 ? (
              <div className="text-center py-20 text-slate-500 text-xs">Waiting for agent events...</div>
            ) : (
              [...events].reverse().map((ev) => {
                const isMilestone = ev.event_type === 'milestone';
                const isWarning = ev.event_type === 'warning';
                return (
                  <div
                    key={ev.id}
                    className={`p-3 rounded-xl border text-xs transition ${
                      isMilestone
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'
                        : isWarning
                        ? 'bg-amber-500/10 border-amber-500/20 text-amber-200'
                        : 'bg-slate-900/50 border-white/5 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="font-semibold text-blue-400 flex items-center gap-1.5">
                        {isMilestone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                        {isWarning && <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />}
                        {!isMilestone && !isWarning && <Info className="w-3.5 h-3.5 text-slate-400" />}
                        <span>[{ev.stage}]</span>
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {ev.timestamp ? ev.timestamp.slice(11, 19) : ''}
                      </span>
                    </div>
                    <p className="leading-relaxed">{ev.message}</p>
                    {ev.file_name && (
                      <div className="mt-1.5 text-[11px] text-slate-400 font-mono flex items-center gap-1">
                        <FileCode className="w-3 h-3 text-slate-500" />
                        <span>{ev.file_name}</span>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Guarded Chat (1 Col) */}
        <div className="glass-panel rounded-2xl p-6 flex flex-col h-[580px]">
          <div className="border-b border-white/5 pb-3 mb-3">
            <h3 className="font-bold text-white text-sm flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-purple-400" />
              <span>Interactive Agent Chat</span>
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Ask progress inquiries or inject context directives (*"focus on payments"*).
            </p>
          </div>

          {/* Messages Container */}
          <div className="overflow-y-auto flex-1 space-y-3 pr-1 mb-3 text-xs">
            {chatMessages.length === 0 ? (
              <div className="text-center py-20 text-slate-500 text-xs leading-relaxed">
                Try asking:<br />
                <span className="text-slate-400 italic">"What are you analyzing so far?"</span>
                <br /><br />
                Or provide directives:<br />
                <span className="text-slate-400 italic">"Focus on payments and deprecate /admin"</span>
              </div>
            ) : (
              chatMessages.map((c) => {
                const isUser = c.role === 'user';
                return (
                  <div
                    key={c.id}
                    className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-[85%] p-3 rounded-2xl ${
                        isUser
                          ? 'bg-blue-600 text-white rounded-br-none'
                          : 'bg-slate-800 text-slate-200 border border-white/5 rounded-bl-none'
                      }`}
                    >
                      <p className="leading-relaxed">{c.content}</p>
                    </div>
                    <span className="text-[10px] text-slate-500 mt-1 px-1">
                      {isUser ? 'You' : 'Agent'}
                    </span>
                  </div>
                );
              })
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat Form */}
          <form onSubmit={handleSendChat} className="flex gap-2 pt-2 border-t border-white/5">
            <input
              type="text"
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              placeholder="Ask question or inject context..."
              disabled={sendingChat}
              className="flex-1 px-3.5 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
            />
            <button
              type="submit"
              disabled={sendingChat || !inputMsg.trim()}
              className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white transition disabled:opacity-50 cursor-pointer"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
