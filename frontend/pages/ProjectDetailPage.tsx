
import React, { useEffect, useState, useRef } from 'react';
import { backend } from '../services/orchestrator';
import { Project, Artifact, LogEntry, EngineerTask } from '../types';
import ArtifactViewer from '../components/ArtifactViewer';
import LivePreview from '../components/LivePreview';
import { 
  Play, RefreshCw, Terminal, Download, Monitor, Code2, Send, 
  Sparkles, Activity, FileText, Layout, Share2, MoreHorizontal,
  ClipboardList, Milestone, BookOpen, Layers, Check, Bot, Globe, Smartphone, Palette, AlertTriangle, Bug, Wrench, Loader2, History, ListChecks, FileCode, X as LucideX, MessageSquare
} from 'lucide-react';

interface ProjectDetailPageProps {
  projectId: string;
  onBack: () => void;
}

const TaskHistoryView: React.FC<{ tasks: EngineerTask[] }> = ({ tasks }) => {
  if (tasks.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-300 dark:text-indigo-900 font-mono gap-3 uppercase tracking-[0.2em] text-[9px] min-h-[300px] font-bold">
        <History size={24} className="opacity-20" />
        AWAITING ENGINEER COMMITS...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-6 animate-fade-in px-4 md:px-0">
      <div className="flex items-center justify-between mb-8 border-b border-slate-200 dark:border-white/5 pb-4">
        <div>
          <h3 className="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight">Engineer Activity Log</h3>
          <p className="text-[10px] text-slate-400 dark:text-indigo-400/40 font-black uppercase tracking-[0.2em] mt-1">Timeline of autonomous engineering tasks</p>
        </div>
        <div className="px-3 py-2 sm:px-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center gap-2 whitespace-nowrap shrink-0 shadow-sm shadow-indigo-500/10 transition-all hover:bg-indigo-500/20">
          <ListChecks size={14} className="shrink-0" />
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest pt-px">
            <span>{tasks.length}</span>
            <span className="opacity-70 font-bold">
              <span className="hidden sm:inline">Tasks Finalized</span>
              <span className="sm:hidden">Tasks</span>
            </span>
          </div>
        </div>
      </div>

      <div className="relative space-y-4">
        {/* Timeline line */}
        <div className="absolute left-[39px] top-4 bottom-4 w-px bg-slate-200 dark:bg-white/5"></div>

        {tasks.slice().reverse().map((task) => (
          <div key={task.id} className="relative flex gap-6 items-start group animate-fade-in">
            <div className="flex flex-col items-center shrink-0 w-20">
              <span className="text-[9px] font-black text-slate-400 dark:text-indigo-400/40 uppercase font-mono mb-2">
                {new Date(task.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
              <div className="w-10 h-10 rounded-2xl bg-white dark:bg-[#121620] border-2 border-slate-100 dark:border-white/5 flex items-center justify-center text-indigo-500 shadow-sm relative z-10 group-hover:border-indigo-500/50 group-hover:shadow-indigo-500/10 transition-all duration-500">
                <FileCode size={18} />
                <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-500 border-2 border-white dark:border-[#121620] flex items-center justify-center">
                   <Check size={8} className="text-white" strokeWidth={4} />
                </div>
              </div>
            </div>

            <div className="flex-1 bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 rounded-3xl p-5 hover:bg-slate-50 dark:hover:bg-white/[0.04] transition-all shadow-sm hover:shadow-md min-w-0">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-black text-slate-900 dark:text-white font-mono tracking-tight truncate mr-2">{task.filename}</h4>
                <span className="text-[9px] font-black px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/10 uppercase tracking-widest shrink-0">Completed</span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-indigo-100/40 font-bold leading-relaxed">{task.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const FaultMonitor: React.FC<{ logs: LogEntry[]; projectId: string; onDismiss: () => void }> = ({ logs, projectId, onDismiss }) => {
  const [fixingIds, setFixingIds] = useState<Set<string>>(new Set());
  const errors = logs.filter(l => l.type === 'error');
  
  if (errors.length === 0) return null;

  const handleFix = async (logId: string) => {
    setFixingIds(prev => new Set(prev).add(logId));
    await backend.fixError(projectId, logId);
    setFixingIds(prev => {
      const next = new Set(prev);
      next.delete(logId);
      return next;
    });
  };

  return (
    <div className="mb-6 p-5 bg-red-500/10 border border-red-500/30 rounded-2xl animate-fade-in relative overflow-hidden group/monitor">
      <div className="absolute top-0 right-0 p-2 z-10">
        <button 
          onClick={(e) => {
            e.stopPropagation();
            onDismiss();
          }}
          className="text-red-500/40 hover:text-red-500 transition-all cursor-pointer p-2 rounded-xl hover:bg-red-500/10 active:scale-90"
          title="Dismiss All Faults"
        >
          <LucideX size={18} />
        </button>
      </div>
      <div className="flex items-center gap-2 mb-5 text-red-500 text-[10px] font-black uppercase tracking-[0.2em]">
        <div className="w-2 h-2 rounded-full bg-red-500 animate-ping"></div>
        Critical Fault Monitor
      </div>
      <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar pr-2">
        {errors.map(err => {
          const isFixing = fixingIds.has(err.id);
          return (
            <div key={err.id} className="flex flex-col sm:flex-row items-start sm:items-center gap-4 bg-white/5 border border-white/5 rounded-2xl p-4 group hover:bg-red-500/[0.03] transition-all">
              <div className="w-8 h-8 rounded-xl bg-red-500/10 flex items-center justify-center text-red-500 shrink-0">
                <AlertTriangle size={14} />
              </div>
              
              <div className="flex-1 space-y-1 w-full">
                <div className="text-[9px] font-mono text-red-500/50 uppercase tracking-widest font-bold">
                  {new Date(err.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </div>
                <div className="text-[11px] font-bold text-slate-800 dark:text-red-200 leading-relaxed break-words">
                  {err.message}
                </div>
              </div>

              <button 
                onClick={() => handleFix(err.id)}
                disabled={isFixing}
                className={`w-full sm:w-auto flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg ${
                  isFixing 
                  ? 'bg-slate-500/20 text-slate-400 cursor-not-allowed' 
                  : 'bg-red-500 text-white hover:bg-red-600 shadow-red-500/20 cursor-pointer active:scale-95'
                }`}
              >
                {isFixing ? (
                  <Loader2 size={12} className="animate-spin" />
                ) : (
                  <Wrench size={12} />
                )}
                {isFixing ? 'Fixing...' : 'Fix Now'}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const AgentStatusMessage: React.FC<{ project: Project; name: string }> = ({ project, name }) => {
  const [textIndex, setTextIndex] = useState(0);
  const statuses = [
    "Analyzing requirements...",
    "Planning architecture...",
    "Generating components...",
    "Writing business logic...",
    "Assembling preview..."
  ];

  useEffect(() => {
    if (project.status === 'RUNNING') {
      const interval = setInterval(() => {
        setTextIndex((prev) => (prev + 1) % statuses.length);
      }, 2500);
      return () => clearInterval(interval);
    }
  }, [project.status]);

  if (project.status === 'RUNNING') {
    return (
      <div className="flex gap-2.5 items-start animate-fade-in mb-4">
        <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-500 shrink-0">
          <Bot size={16} />
        </div>
        <div className="bg-white dark:bg-[#121620] border border-slate-200 dark:border-white/5 rounded-2xl px-5 py-3 flex items-center gap-3 min-w-[200px] shadow-sm">
          <div className="w-4 h-4 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin shrink-0"></div>
          <span key={textIndex} className="text-[11px] text-slate-800 dark:text-indigo-100 font-bold animate-fade-in">
            {statuses[textIndex]}
          </span>
        </div>
      </div>
    );
  }

  if (project.status === 'COMPLETED') {
    return (
      <div className="flex gap-2.5 items-start animate-fade-in mb-4">
        <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-500 shrink-0">
          <Bot size={16} />
        </div>
        <div className="bg-white dark:bg-[#121620] border border-slate-200 dark:border-white/5 rounded-2xl p-5 space-y-4 w-full shadow-lg dark:shadow-indigo-500/10">
          <div className="text-[11px] text-slate-900 dark:text-indigo-100 font-bold leading-relaxed">
            I've built <span className="text-indigo-600 dark:text-indigo-400 font-black italic">"{name}"</span> for you. The preview is ready â€” check it out on the right!
          </div>
          <div className="h-[1px] bg-slate-100 dark:bg-white/5 w-full"></div>
          <div className="space-y-2">
            {statuses.map((s, i) => (
              <div key={i} className="flex items-center gap-2.5 text-[10px] text-slate-600 dark:text-indigo-200 font-bold animate-fade-in">
                <Check size={12} className="text-indigo-600 dark:text-indigo-400" />
                <span>{s}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

const chatSuggestions = [
  { label: 'Add dark mode', icon: Activity },
  { label: 'Improve UI', icon: Palette },
  { label: 'Add charts', icon: Activity },
  { label: 'Mobile fix', icon: Smartphone }
];

const ChatMessage: React.FC<{ log: LogEntry }> = ({ log }) => {
  const isUser = log.message.startsWith('User:');
  const isSuccess = log.type === 'success';
  const cleanMessage = log.message.replace('User: ', '');

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {!isUser && (
        <div className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 transition-all duration-500 ${
          isSuccess 
          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 shadow-[0_0_10px_rgba(16,185,129,0.1)]' 
          : 'bg-indigo-500/10 border-indigo-500/20 text-indigo-500'
        }`}>
          {isSuccess ? <Check size={14} className="animate-fade-in" /> : <Bot size={16} />}
        </div>
      )}
      <div className={`max-w-[90%] rounded-2xl p-4 text-[11px] leading-relaxed font-bold shadow-sm transition-all duration-500 ${
        isUser 
        ? 'bg-gradient-to-br from-indigo-500 to-violet-600 text-white self-end shadow-md shadow-indigo-500/10' 
        : isSuccess
        ? 'bg-emerald-50 dark:bg-emerald-500/5 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 animate-fade-in'
        : 'bg-white dark:bg-white/[0.03] border border-slate-200 dark:border-white/5 text-slate-800 dark:text-indigo-50'
      }`}>
        {cleanMessage}
        {isSuccess && <Check size={10} className="inline-block ml-1.5 mb-0.5 text-emerald-500" />}
      </div>
    </div>
  );
};

const ProjectDetailPage: React.FC<ProjectDetailPageProps> = ({ projectId }) => {
  const [project, setProject] = useState<Project | undefined>(undefined);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [activeTab, setActiveTab] = useState<'preview' | 'brief' | 'prd' | 'architecture' | 'code' | 'tasks' | 'terminal'>('preview');
  const [chatInput, setChatInput] = useState('');
  const [progress, setProgress] = useState(0);
  const [showMobileChat, setShowMobileChat] = useState(false); // Mobile state toggle
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const update = () => {
      const p = backend.getProject(projectId);
      setProject(p);
      setArtifacts(backend.getArtifacts(projectId));
      setLogs(backend.getLogs(projectId));
    };
    update();
    const unsubscribe = backend.subscribe(update);
    return unsubscribe;
  }, [projectId]);

  useEffect(() => {
    if (project?.status !== 'RUNNING') {
      setProgress(0);
      return;
    }

    const interval = setInterval(() => {
      setProgress(prev => {
        let target = 0;
        switch(project.currentStage) {
          case 'pm': target = 33; break;
          case 'planner': target = 66; break;
          case 'engineer': target = 95; break;
          default: target = 100;
        }

        if (prev < target) return prev + 1;
        if (prev < 99) return prev + 0.1;
        return prev;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [project?.status, project?.currentStage]);

  useEffect(() => {
    if (logsEndRef.current) {
        logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  if (!project) return <div className="flex items-center justify-center h-full bg-background-light dark:bg-[#0b0e14] text-indigo-500 font-mono text-xs animate-pulse font-bold">INITIALIZING ENVIRONMENT...</div>;

  const prdArtifact = artifacts.find(a => a.type === 'PRD');
  const planArtifact = artifacts.find(a => a.type === 'PLAN');
  const codeArtifact = artifacts.find(a => a.type === 'CODE');
  const hasCode = !!codeArtifact;
  const errorCount = logs.filter(l => l.type === 'error').length;

  const getStatusText = () => {
    switch(project.currentStage) {
      case 'pm': return 'Analyzing requirements...';
      case 'planner': return 'Architecting solution...';
      case 'engineer': return 'Assembling preview...';
      default: return 'Initializing...';
    }
  };

  const handleSendChat = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    backend.addLog(projectId, `User: ${chatInput}`, 'info');
    setChatInput('');
  };

  const filteredLogs = logs.filter(l => {
    // Suppress file-level engineer writes (too noisy for chat)
    if (l.message.includes('Engineer Agent: Completed')) return false;
    // Suppress "Workflow completed successfully" - the AgentStatusMessage below replaces it
    if (l.message === 'Workflow completed successfully.') return false;

    if (l.type === 'info' || l.type === 'success') {
      const isInternalNoisy = (l.message.includes('Analyzing requirements') || 
                               l.message.includes('Architecting') || 
                               l.message.includes('Writing code') ||
                               l.message.includes('Starting execution pipeline')) && !l.message.includes('User:');
      
      if (l.message.includes('Agent patching:') || l.message.includes('Recovery Successful:')) return true;
      
      return !isInternalNoisy;
    }
    return false;
  });

  const completionLog = logs.find(l => l.message === "Workflow completed successfully.");
  const completionTime = completionLog ? completionLog.timestamp : Infinity;

  const buildLogs = filteredLogs.filter(l => l.timestamp <= completionTime);
  const followUpLogs = filteredLogs.filter(l => l.timestamp > completionTime);

  const handleInjectError = () => {
    backend.injectSimulatedError(projectId);
  };

  const handleDismissFaults = () => {
    backend.clearErrors(projectId);
  };

  const getTechColor = (tech: string) => {
    const lower = tech.toLowerCase();
    if (lower.includes('frontend')) return 'text-blue-600 dark:text-blue-400';
    if (lower.includes('styling')) return 'text-pink-600 dark:text-pink-400';
    if (lower.includes('backend')) return 'text-emerald-600 dark:text-emerald-400';
    if (lower.includes('database')) return 'text-amber-600 dark:text-amber-400';
    if (lower.includes('state')) return 'text-violet-600 dark:text-violet-400';
    return 'text-indigo-600 dark:text-indigo-400';
  };

  const tabs = [
    { id: 'preview', icon: Monitor, label: 'Preview' },
    { id: 'brief', icon: BookOpen, label: 'Brief' },
    { id: 'prd', icon: ClipboardList, label: 'PRD' },
    { id: 'architecture', icon: Milestone, label: 'Plan' },
    { id: 'code', icon: Code2, label: 'Code' },
    { id: 'tasks', icon: History, label: 'Tasks' },
    { id: 'terminal', icon: Terminal, label: 'Logs', badge: errorCount }
  ];

  return (
    <div className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-[#0b0e14] relative transition-colors duration-300">
      <header className="h-14 border-b border-slate-200 dark:border-white/5 flex items-center justify-between px-3 md:px-5 bg-white/80 dark:bg-[#080a0f]/80 backdrop-blur-xl relative z-[60] shrink-0">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="text-[11px] font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2 truncate">
            <span className="text-slate-400 dark:text-indigo-400/60 font-bold uppercase text-[9px] pt-0.5 hidden sm:inline">Projects /</span>
            <span className="truncate">{project.name}</span>
          </div>
          <div className={`px-2 py-0.5 rounded-lg text-[8px] uppercase tracking-widest font-black border shrink-0 ${
            project.status === 'RUNNING' ? 'border-indigo-500/40 text-indigo-600 dark:text-indigo-400 bg-indigo-500/10 animate-pulse' : 'border-slate-200 dark:border-slate-800 text-slate-400'
          }`}>
            {project.status}
          </div>
        </div>

        <div className="flex items-center gap-2 md:gap-3">
          
          {/* Desktop Navigation Tabs */}
          <div className="hidden lg:flex items-center bg-slate-100 dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/5 p-1 overflow-x-auto no-scrollbar max-w-[200px] sm:max-w-none">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => {
                   setActiveTab(tab.id as any);
                   setShowMobileChat(false);
                }}
                className={`relative flex items-center gap-1.5 px-2 md:px-3 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all whitespace-nowrap ${
                  activeTab === tab.id 
                    ? 'bg-gradient-to-br from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-500/20' 
                    : 'text-slate-500 dark:text-indigo-300 hover:text-indigo-600 dark:hover:text-indigo-50 cursor-pointer'
                } ${tab.id === 'terminal' && errorCount > 0 ? 'shadow-[0_0_15px_rgba(239,68,68,0.2)]' : ''}`}
              >
                <tab.icon size={13} />
                <span className="hidden xl:inline">{tab.label}</span>
                {tab.id === 'terminal' && errorCount > 0 && (
                  <span className="absolute -top-1.5 -right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[8px] flex items-center justify-center font-black animate-pulse border-2 border-white dark:border-[#080a0f]">
                    {errorCount}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Mobile Navigation Controls */}
          <div className="lg:hidden flex items-center gap-2">
             <div className="flex items-center bg-slate-100 dark:bg-white/5 rounded-full p-1 border border-slate-200 dark:border-white/5">
                <button
                   onClick={() => { setShowMobileChat(true); setIsMobileMenuOpen(false); }}
                   className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all ${
                     showMobileChat 
                       ? 'bg-white dark:bg-[#1a1f2e] text-indigo-600 dark:text-white shadow-sm' 
                       : 'text-slate-500 dark:text-slate-400'
                   }`}
                >
                   Chat
                </button>
                <button
                   onClick={() => { setShowMobileChat(false); setActiveTab('preview'); setIsMobileMenuOpen(false); }}
                   className={`px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all ${
                     !showMobileChat && activeTab === 'preview' 
                       ? 'bg-white dark:bg-[#1a1f2e] text-indigo-600 dark:text-white shadow-sm' 
                       : 'text-slate-500 dark:text-slate-400'
                   }`}
                >
                   Preview
                </button>
             </div>

             <div className="relative">
                <button
                   onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                   className={`w-9 h-9 flex items-center justify-center rounded-full border transition-all ${
                     isMobileMenuOpen || (!showMobileChat && activeTab !== 'preview')
                       ? 'bg-white dark:bg-[#1a1f2e] border-indigo-500/30 text-indigo-600 dark:text-white shadow-sm' 
                       : 'bg-slate-100 dark:bg-white/5 border-slate-200 dark:border-white/5 text-slate-500 dark:text-slate-400'
                   }`}
                >
                   <MoreHorizontal size={16} />
                   {errorCount > 0 && (
                      <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-red-500 border-2 border-white dark:border-[#080a0f]"></span>
                   )}
                </button>
                
                {isMobileMenuOpen && (
                   <>
                      <div className="fixed inset-0 z-40 bg-transparent" onClick={() => setIsMobileMenuOpen(false)}></div>
                      <div className="absolute top-full right-0 mt-2 w-48 bg-white dark:bg-[#1a1f2e] border border-slate-200 dark:border-white/10 rounded-2xl shadow-xl overflow-hidden py-1 z-50 animate-fade-in-up">
                         {tabs.filter(t => t.id !== 'code' && t.id !== 'preview').map(tab => (
                            <button
                               key={tab.id}
                               onClick={() => {
                                  setActiveTab(tab.id as any);
                                  setShowMobileChat(false);
                                  setIsMobileMenuOpen(false);
                               }}
                               className={`w-full flex items-center gap-3 px-4 py-3 text-[10px] font-bold uppercase tracking-wider transition-colors ${
                                  activeTab === tab.id && !showMobileChat
                                     ? 'bg-indigo-5 dark:bg-white/5 text-indigo-600 dark:text-white' 
                                     : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5'
                               }`}
                            >
                               <tab.icon size={14} />
                               {tab.label}
                               {tab.id === 'terminal' && errorCount > 0 && (
                                  <span className="ml-auto bg-red-500 text-white text-[9px] px-1.5 py-0.5 rounded-full">
                                     {errorCount}
                                  </span>
                               )}
                            </button>
                         ))}
                      </div>
                   </>
                )}
             </div>
          </div>
          
          <div className="hidden sm:block w-[1px] h-4 bg-slate-200 dark:bg-white/10 mx-1"></div>
          
          <button className="hidden sm:block bg-gradient-to-br from-indigo-600 to-violet-600 hover:brightness-110 text-white px-4 py-2 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all shadow-lg shadow-indigo-500/20 cursor-pointer">
            Deploy
          </button>
        </div>
      </header>

      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden relative">
        
        {/* Chat / Agent Sidebar - Toggleable on Mobile */}
        <div className={`
          ${showMobileChat ? 'flex' : 'hidden'} lg:flex 
          w-full lg:w-72 xl:w-[320px] 
          border-b lg:border-b-0 lg:border-r border-slate-200 dark:border-white/5 
          flex-col bg-slate-50 dark:bg-[#080a0f] relative z-20 
          absolute inset-0 lg:static h-full
        `}>
          <div className="flex-1 overflow-y-auto p-5 space-y-6 custom-scrollbar">
            <div className="bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 rounded-2xl p-4 text-[11px] leading-relaxed text-slate-800 dark:text-indigo-50 font-bold shadow-sm">
              <div className="text-indigo-600 dark:text-indigo-400 font-black mb-2 uppercase tracking-widest flex items-center gap-1.5 text-[9px]">
                <Sparkles size={11} />
                PROMPT
              </div>
              {project.description}
            </div>

            <div className="space-y-4">
              {buildLogs.map(log => (
                <ChatMessage key={log.id} log={log} />
              ))}

              {(project.status === 'RUNNING' || project.status === 'COMPLETED') && (
                <AgentStatusMessage project={project} name={project.name} />
              )}

              {followUpLogs.map(log => (
                <ChatMessage key={log.id} log={log} />
              ))}
              
              <div ref={logsEndRef} />
            </div>
          </div>

          <div className="p-4 bg-white dark:bg-[#0a0d14] border-t border-slate-200 dark:border-white/5 space-y-3">
            <div className="flex gap-2 overflow-x-auto custom-scrollbar no-scrollbar pb-1">
              {chatSuggestions.map((s, idx) => (
                <button 
                  key={idx}
                  onClick={() => setChatInput(s.label)}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-50 dark:bg-white/[0.03] border border-slate-200 dark:border-white/5 text-[9px] font-bold text-slate-600 dark:text-indigo-100/40 whitespace-nowrap hover:bg-indigo-50 dark:hover:bg-white/10 hover:text-indigo-600 dark:hover:text-indigo-300 transition-all uppercase tracking-tighter cursor-pointer"
                >
                  <s.icon size={11} className="text-indigo-500/50" />
                  {s.label}
                </button>
              ))}
            </div>

            <form onSubmit={handleSendChat} className="relative group/form">
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/0 via-indigo-500/10 to-indigo-500/0 rounded-[1.25rem] opacity-0 group-focus-within/form:opacity-100 blur transition-opacity duration-700 pointer-events-none"></div>
              <textarea 
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask for changes..."
                className="w-full bg-slate-50 dark:bg-[#121620] border border-slate-200 dark:border-white/10 rounded-2xl pl-4 pr-12 py-3.5 text-[11px] text-slate-900 dark:text-indigo-50 focus:outline-none focus:border-indigo-500/40 focus:ring-4 focus:ring-indigo-500/5 focus:bg-white dark:focus:bg-[#1a1f2e] min-h-[48px] max-h-[160px] resize-none font-bold placeholder:text-slate-400 dark:placeholder:text-indigo-400/30 shadow-inner transition-all overflow-y-auto custom-scrollbar relative z-10"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendChat(e);
                  }
                }}
              />
              <button 
                type="submit"
                disabled={!chatInput.trim()}
                className="absolute right-3.5 bottom-3.5 p-1.5 text-indigo-500 hover:text-indigo-700 dark:hover:text-white transition-all cursor-pointer disabled:cursor-not-allowed disabled:opacity-30 z-20 hover:scale-110 active:scale-90"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>

        {/* Main Workspace - Hidden on Mobile if Chat is open */}
        <div className={`${showMobileChat ? 'hidden' : 'flex'} lg:flex flex-1 relative overflow-hidden flex-col bg-slate-100 dark:bg-[#0b0e14]`}>
          {project.status === 'RUNNING' && activeTab !== 'tasks' && activeTab !== 'terminal' && (
            <div className="absolute inset-0 z-40 bg-slate-50 dark:bg-[#0b0e14] flex flex-col items-center justify-center animate-fade-in p-10 text-center">
              <div className="w-full max-w-4xl flex flex-col items-center gap-8">
                <div className="relative w-24 h-24 flex items-center justify-center">
                  <div className="absolute inset-0 border-[2px] border-indigo-500/20 rounded-[2rem] rotate-45 animate-spin-slow shadow-[0_0_30px_rgba(99,102,241,0.05)]"></div>
                  <div className="absolute inset-2 border border-violet-500/10 rounded-[1.6rem] -rotate-45 animate-spin-slow duration-[8s] opacity-50"></div>
                  <div className="w-12 h-12 rounded-full border-[3px] border-indigo-500/10 border-t-indigo-500 animate-spin relative shadow-[0_0_25px_rgba(99,102,241,0.2)]"></div>
                </div>
                
                <div className="w-full max-w-md space-y-6">
                  <div className="text-slate-800 dark:text-white font-black text-sm tracking-wide uppercase">
                    {getStatusText()}
                  </div>
                  
                  <div className="w-full h-2 bg-slate-200 dark:bg-white/5 rounded-full overflow-hidden shadow-inner border border-slate-300/50 dark:border-white/5">
                    <div 
                      className="h-full bg-gradient-to-r from-[#a855f7] via-[#6366f1] via-[#3b82f6] to-[#2dd4bf] transition-all duration-300 ease-out shadow-[0_0_15px_rgba(45,212,191,0.1)]"
                      style={{ width: `${Math.floor(progress)}%` }}
                    ></div>
                  </div>
                  
                  <div className="text-[11px] font-mono text-indigo-600 dark:text-indigo-400/50 uppercase tracking-[0.2em] font-black">
                    {Math.floor(progress)}%
                  </div>
                </div>
              </div>
              <div className="absolute inset-0 bg-grid-pattern opacity-[0.05] pointer-events-none"></div>
            </div>
          )}

          <div className={`flex-1 p-4 md:p-6 overflow-hidden transition-opacity duration-500 ${project.status === 'RUNNING' && activeTab !== 'tasks' && activeTab !== 'terminal' ? 'opacity-0' : 'opacity-100'}`}>
            {activeTab === 'preview' && (
              <div className="h-full animate-fade-in">
                <LivePreview code={codeArtifact?.content} projectName={project.name} />
              </div>
            )}

            {activeTab === 'brief' && (
              <div className="h-full overflow-y-auto custom-scrollbar animate-fade-in">
                <div className="max-w-4xl mx-auto py-2 md:py-6">
                  {prdArtifact ? (
                    <div className="space-y-12">
                      <div className="text-center space-y-3 mb-16">
                        <h2 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">{prdArtifact.content.title}</h2>
                        <div className="flex items-center justify-center gap-3 text-slate-400 dark:text-indigo-400/40 text-[9px] font-mono uppercase tracking-[0.2em]">
                          <span>Status: Finalized</span>
                          <span className="w-1 h-1 bg-slate-300 dark:bg-indigo-900 rounded-full"></span>
                          <span>Version: 1.0.0-Stable</span>
                        </div>
                      </div>

                      <section className="space-y-6">
                        <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold uppercase tracking-[0.2em] text-[9px]">
                          <BookOpen size={14} />
                          Overview
                        </div>
                        <div className="text-base text-slate-800 dark:text-indigo-50 leading-relaxed font-bold bg-white dark:bg-white/[0.01] border border-slate-200 dark:border-white/5 p-8 rounded-3xl shadow-xl shadow-slate-200/50 dark:shadow-indigo-500/5">
                          {prdArtifact.content.summary}
                        </div>
                      </section>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <section className="space-y-6">
                          <div className="flex items-center gap-2 text-violet-600 dark:text-violet-400 font-bold uppercase tracking-[0.2em] text-[9px]">
                            <Sparkles size={14} />
                            Key Components
                          </div>
                          <div className="space-y-2.5">
                            {prdArtifact.content.features.map((f: string, i: number) => (
                              <div key={i} className="flex gap-3.5 p-4 rounded-2xl bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 group hover:border-indigo-500/20 transition-all cursor-default shadow-sm hover:shadow-md">
                                <div className="w-6 h-6 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 flex items-center justify-center text-[9px] font-black shrink-0">
                                  {i + 1}
                                </div>
                                <span className="text-xs text-slate-800 dark:text-indigo-100 group-hover:text-indigo-600 dark:group-hover:text-white transition-colors font-bold">{f}</span>
                              </div>
                            ))}
                          </div>
                        </section>

                        <section className="space-y-6">
                          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold uppercase tracking-[0.2em] text-[9px]">
                            <Layers size={14} />
                            Technology Map
                          </div>
                          <div className="bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 rounded-3xl p-6 divide-y divide-slate-100 dark:divide-white/5 shadow-sm">
                            {prdArtifact.content.techStackRecommendation.map((t: string, i: number) => (
                              <div key={i} className="py-3.5 first:pt-0 last:pb-0 text-[11px] flex items-center justify-between font-bold group">
                                {(() => {
                                  const colonIdx = t.indexOf(':');
                                  const label = colonIdx > -1 ? t.slice(0, colonIdx).trim() : t.trim();
                                  const value = colonIdx > -1 ? t.slice(colonIdx + 1).trim() : '';
                                  return (
                                    <>
                                      <span className="text-slate-500 dark:text-indigo-200/40 uppercase tracking-tighter group-hover:text-slate-900 dark:group-hover:text-white transition-colors">{label}</span>
                                      {value && <span className={`text-[10px] font-mono ${getTechColor(label)} group-hover:brightness-125 transition-all`}>{value}</span>}
                                    </>
                                  );
                                })()}
                              </div>
                            ))}
                          </div>
                        </section>
                      </div>
                    </div>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-300 dark:text-indigo-900 font-mono gap-3 uppercase tracking-[0.2em] text-[9px] min-h-[300px] font-bold">
                      <BookOpen size={24} className="opacity-20" />
                      GENERATING ARCHITECTURE BRIEF...
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {activeTab === 'prd' && (
              <div className="h-full animate-fade-in pr-2">
                <div className="max-w-4xl mx-auto py-2 h-full">
                  {prdArtifact ? (
                    <ArtifactViewer artifact={prdArtifact} />
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-300 dark:text-indigo-900 font-mono gap-3 uppercase tracking-[0.2em] text-[9px] min-h-[300px] font-bold">
                      <ClipboardList size={24} className="opacity-20" />
                      AWAITING PRD SYNCHRONIZATION...
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'architecture' && (
              <div className="h-full animate-fade-in pr-2">
                <div className="max-w-4xl mx-auto py-2 h-full">
                  {planArtifact ? (
                    <ArtifactViewer artifact={planArtifact} />
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-300 dark:text-indigo-900 font-mono gap-3 uppercase tracking-[0.2em] text-[9px] min-h-[300px] font-bold">
                      <Milestone size={24} className="opacity-20" />
                      DESIGNING INFRASTRUCTURE ROADMAP...
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'code' && (
              <div className="h-full overflow-auto custom-scrollbar animate-fade-in pr-2">
                <div className="max-w-5xl mx-auto py-2 h-full">
                  {hasCode ? (
                    <ArtifactViewer artifact={codeArtifact} />
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-300 dark:text-indigo-900 font-mono gap-3 uppercase tracking-[0.2em] text-[9px] min-h-[300px] font-bold">
                       <Code2 size={24} className="opacity-20" />
                       SYNTHESIZING CODEBASE...
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'tasks' && (
              <div className="h-full overflow-y-auto custom-scrollbar animate-fade-in">
                <TaskHistoryView tasks={project.engineerTasks || []} />
              </div>
            )}

            {activeTab === 'terminal' && (
              <div className="h-full overflow-hidden bg-slate-50 dark:bg-black rounded-3xl border border-slate-200 dark:border-white/5 shadow-2xl animate-fade-in flex flex-col font-mono text-[11px]">
                 <div className="p-3 bg-white dark:bg-[#111] border-b border-slate-200 dark:border-white/5 text-[9px] text-indigo-600 dark:text-indigo-800 uppercase tracking-widest font-black flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Terminal size={14} />
                      Runtime Environment Logs
                    </div>
                    <div className="flex items-center gap-4">
                      {errorCount > 0 && (
                        <div className="flex items-center gap-2 text-red-500 animate-pulse hidden sm:flex">
                          <AlertTriangle size={12} />
                          <span>{errorCount} FAULT(S) DETECTED</span>
                        </div>
                      )}
                      <button 
                        onClick={handleInjectError}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all cursor-pointer group active:scale-95 ${
                          errorCount > 0 
                          ? 'bg-red-500 text-white border-red-400 animate-pulse shadow-[0_0_20px_rgba(239,68,68,0.6)] hover:brightness-110' 
                          : 'bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 border-red-500/20'
                        }`}
                      >
                        {errorCount > 0 ? (
                          <AlertTriangle size={12} className="animate-bounce" />
                        ) : (
                          <Bug size={12} className="group-hover:rotate-12 transition-transform" />
                        )}
                        <span className="hidden sm:inline">Simulate Fault</span>
                        <span className="sm:hidden">Fault</span>
                      </button>
                    </div>
                 </div>
                 <div className="flex-1 p-6 overflow-y-auto custom-scrollbar relative bg-white dark:bg-black">
                    <div className="absolute inset-0 scanlines opacity-5 dark:opacity-20 pointer-events-none"></div>
                    <FaultMonitor logs={logs} projectId={projectId} onDismiss={handleDismissFaults} />
                    <div className="space-y-2">
                      {logs.map(log => {
                        const isWorkflow = log.message === 'Workflow completed successfully.';
                        const isCodeDone = log.message === 'Engineer Agent: Code generation complete.';
                        const isFileWrite = log.message.startsWith('Engineer Agent: Completed ');
                        const logColor = log.type === 'error' ? 'text-red-600 dark:text-red-400'
                          : isWorkflow ? 'text-violet-500 dark:text-violet-400 font-black'
                          : isCodeDone ? 'text-emerald-600 dark:text-emerald-400 font-black'
                          : isFileWrite ? 'text-slate-700 dark:text-slate-100'
                          : log.type === 'success' ? 'text-emerald-600 dark:text-emerald-400 font-black'
                          : log.type === 'system' ? 'text-indigo-600 dark:text-indigo-400 font-black'
                          : 'text-slate-700 dark:text-slate-100';
                        return (
                          <div key={log.id} className="mb-2 flex gap-2 sm:gap-5 items-start">
                            <span className="text-slate-400 dark:text-slate-600 shrink-0 font-mono text-[10px] pt-0.5">{new Date(log.timestamp).toLocaleTimeString([], {hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
                            <span className={`font-bold break-words w-full ${logColor}`}>{log.message}</span>
                          </div>
                        );
                      })}
                    </div>
                 </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetailPage;


