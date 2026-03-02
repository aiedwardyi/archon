
import React, { useState } from 'react';
import { Artifact, PrdResponse, PlanResponse } from '../types';
import { FileCode, FileText, Layout, Copy, Terminal, ChevronRight, CheckCircle2, Clock, Map, Hash, Wand2, Loader2, Check } from 'lucide-react';

interface ArtifactViewerProps {
  artifact: Artifact;
}

const SyntaxHighlighter: React.FC<{ code: string; language: string }> = ({ code, language }) => {
  const highlight = (text: string) => {
    if (!text) return text;

    let tokens = [
      { regex: /(\/\/.*$|\/\*[\s\S]*?\*\/)/gm, class: 'text-slate-400 dark:text-slate-500 italic' },
      { regex: /(["'])(?:(?=(\\?))\2.)*?\1/g, class: 'text-emerald-600 dark:text-emerald-400' },
      { regex: /\b(export|class|async|await|import|from|return|const|let|var|function|if|else|for|while|interface|type|default|extends|new|try|catch|finally|throw)\b/g, class: 'text-indigo-600 dark:text-purple-400 font-bold' },
      { regex: /\b(true|false|null|undefined|\d+)\b/g, class: 'text-amber-600 dark:text-amber-500' },
      { regex: /\b([a-z_][a-zA-Z0-9_]*)(?=\s*\()/g, class: 'text-blue-600 dark:text-blue-400' },
      { regex: /\b([A-Z][a-zA-Z0-9_]*)\b/g, class: 'text-indigo-800 dark:text-yellow-200' },
      { regex: /\b([a-z_][a-zA-Z0-9_]*)(?=\s*:)/g, class: 'text-rose-600 dark:text-rose-400' },
    ];

    let highlighted: { text: string; isHighlighted: boolean; className?: string }[] = [{ text, isHighlighted: false }];

    tokens.forEach((token) => {
      let nextHighlighted: { text: string; isHighlighted: boolean; className?: string }[] = [];
      highlighted.forEach((segment) => {
        if (segment.isHighlighted) {
          nextHighlighted.push(segment);
          return;
        }

        let lastIndex = 0;
        let match;
        const regex = new RegExp(token.regex);
        
        while ((match = regex.exec(segment.text)) !== null) {
          if (match.index > lastIndex) {
            nextHighlighted.push({
              text: segment.text.substring(lastIndex, match.index),
              isHighlighted: false,
            });
          }
          nextHighlighted.push({
            text: match[0],
            isHighlighted: true,
            className: token.class,
          });
          lastIndex = regex.lastIndex;
          if (regex.lastIndex === match.index) regex.lastIndex++;
        }

        if (lastIndex < segment.text.length) {
          nextHighlighted.push({
            text: segment.text.substring(lastIndex),
            isHighlighted: false,
          });
        }
      });
      highlighted = nextHighlighted;
    });

    return highlighted.map((segment, i) => (
      segment.isHighlighted ? 
        <span key={i} className={segment.className}>{segment.text}</span> : 
        <span key={i}>{segment.text}</span>
    ));
  };

  const lines = code.split('\n');

  return (
    <div className="flex font-mono text-[12px] leading-relaxed relative group bg-white dark:bg-[#080a0f]">
      <div className="flex flex-col text-right pr-4 border-r border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-[#080a0f] text-slate-400 dark:text-slate-600 select-none min-w-[3.5rem] py-8">
        {lines.map((_, i) => (
          <div key={i} className="h-[1.5em] leading-none flex items-center justify-end">{i + 1}</div>
        ))}
      </div>
      
      <div className="flex-1 overflow-x-auto py-8 pl-6 relative text-slate-900 dark:text-slate-300">
        <div className="absolute inset-0 scanlines opacity-[0.02] dark:opacity-5 pointer-events-none"></div>
        <pre className="relative z-10 whitespace-pre">
          {lines.map((line, i) => (
            <div key={i} className="h-[1.5em] flex items-center hover:bg-slate-100 dark:hover:bg-white/[0.03] -ml-6 pl-6 transition-colors">
              {highlight(line)}
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
};

const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact }) => {
  const [activeFile, setActiveFile] = useState<number>(0);

  const renderContent = () => {
    if (artifact.type === 'CODE') {
        const files = artifact.content.files || [];
        if(files.length === 0) return <div className="p-8 text-indigo-900 dark:text-indigo-400 text-center italic font-bold">No files generated.</div>;
        
        const currentContent = files[activeFile]?.content || '';

        return (
          <div className="flex flex-col md:flex-row h-full min-h-[550px] bg-white dark:bg-[#080a0f]">
             {/* File Explorer */}
             <div className="w-full md:w-60 h-40 md:h-auto border-b md:border-b-0 md:border-r border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-[#080a0f] flex flex-col shrink-0">
               <div className="p-4 flex items-center justify-between border-b border-slate-200 dark:border-white/5 bg-white dark:bg-[#0a0d14]/50">
                 <div className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-widest">Explorer</div>
                 <Hash size={12} className="text-slate-300 dark:text-slate-700" />
               </div>
               <div className="p-2 space-y-1 overflow-y-auto custom-scrollbar flex-1">
                 {files.map((f: any, idx: number) => (
                   <button 
                    key={idx}
                    onClick={() => setActiveFile(idx)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 text-[11px] font-mono rounded-xl transition-all focus:outline-none focus:ring-0 group border ${
                      activeFile === idx 
                      ? 'bg-indigo-600/10 text-indigo-700 dark:text-white border-indigo-500/30 shadow-sm' 
                      : 'text-slate-500 dark:text-indigo-200/40 hover:text-indigo-600 dark:hover:text-white hover:bg-white dark:hover:bg-white/5 border-transparent'
                    }`}
                   >
                     <FileCode size={14} className={activeFile === idx ? 'text-indigo-600 dark:text-indigo-400' : 'text-slate-300 dark:text-slate-700 group-hover:text-indigo-400'} />
                     <span className="truncate text-left flex-1 font-bold">{f.filename}</span>
                   </button>
                 ))}
               </div>
             </div>

             {/* Code Editor */}
             <div className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-[#080a0f]">
                <div className="h-10 bg-slate-50 dark:bg-[#0a0d14] border-b border-slate-200 dark:border-white/5 flex items-center px-4 gap-2">
                   <div className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-[#080a0f] border-x border-t border-slate-200 dark:border-white/5 rounded-t-lg -mb-[1px] relative z-10">
                      <FileCode size={12} className="text-indigo-600 dark:text-indigo-400" />
                      <span className="text-[10px] font-bold text-slate-800 dark:text-slate-300 font-mono">{files[activeFile]?.filename}</span>
                   </div>
                   
                   <div className="ml-auto flex items-center gap-3">
                      <div className="flex items-center gap-2 text-[9px] font-bold text-slate-400 dark:text-slate-600 uppercase tracking-widest">
                        <span>{files[activeFile]?.language || 'plaintext'}</span>
                        <div className="w-1.5 h-1.5 rounded-full bg-indigo-500/50"></div>
                      </div>
                   </div>
                </div>

                <div className="flex-1 overflow-auto custom-scrollbar">
                  <SyntaxHighlighter 
                    code={currentContent} 
                    language={files[activeFile]?.language || 'typescript'} 
                  />
                </div>
             </div>
          </div>
        );
    }

    if (artifact.type === 'PRD') {
        const prd = artifact.content as PrdResponse;
        return (
            <div className="bg-white dark:bg-[#0f111a] p-6 md:p-10 space-y-10 font-sans relative h-full overflow-y-auto custom-scrollbar">
                <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none"></div>
                
                <div className="space-y-4 relative z-10">
                    <h3 className="text-2xl font-black text-slate-900 dark:text-white border-b border-slate-200 dark:border-white/10 pb-4">Product Requirements Document</h3>
                    <p className="text-slate-600 dark:text-indigo-100/60 leading-relaxed font-bold">{prd.summary}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-10 relative z-10 pb-10">
                    <div className="space-y-6">
                        <h4 className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-[0.2em]">Functional Scope</h4>
                        <ul className="space-y-3">
                            {prd.features.map((f, i) => (
                                <li key={i} className="flex gap-3 text-xs items-start text-slate-700 dark:text-indigo-100/80 font-bold">
                                    <CheckCircle2 size={16} className="text-indigo-600 dark:text-indigo-500 shrink-0 mt-[-1px]" />
                                    <span>{f}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="space-y-6">
                        <h4 className="text-[10px] font-bold text-violet-600 dark:text-violet-400 uppercase tracking-[0.2em]">User Context</h4>
                        <ul className="space-y-3">
                            {prd.userStories.map((s, i) => (
                                <li key={i} className="flex gap-3 text-xs items-start italic text-slate-400 dark:text-indigo-300/40 font-bold">
                                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-600/30 dark:bg-indigo-500/30 mt-1.5 shrink-0" />
                                    <span>"{s}"</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>
        );
    }

    if (artifact.type === 'PLAN') {
        const plan = artifact.content as PlanResponse;
        return (
            <div className="bg-white dark:bg-[#0f111a] p-6 md:p-10 space-y-8 relative h-full overflow-y-auto custom-scrollbar">
                <div className="absolute inset-0 bg-grid-pattern opacity-[0.03] pointer-events-none"></div>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 dark:border-white/10 pb-6 relative z-10 gap-4">
                    <h3 className="text-xl font-black text-slate-900 dark:text-white">System Architecture & Roadmap</h3>
                    <div className="flex items-center gap-2 text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-widest bg-indigo-500/10 px-3 py-1 rounded-full border border-indigo-500/20 w-fit">
                        <Clock size={12} />
                        Cycle: {plan.estimatedTimeline}
                    </div>
                </div>

                <div className="space-y-12 relative z-10 pb-10">
                    {plan.phases.map((phase, idx) => (
                        <div key={idx} className="relative pl-8 border-l border-slate-200 dark:border-white/10">
                            <div className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-indigo-600 border-4 border-white dark:border-[#0f111a]" />
                            <div className="space-y-4">
                                <div>
                                    <h4 className="text-lg font-black text-slate-900 dark:text-white">{phase.name}</h4>
                                    <p className="text-sm text-slate-500 dark:text-indigo-300/40 mt-1 font-bold">{phase.description}</p>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {phase.steps.map((step, i) => (
                                        <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/5 text-[11px] text-slate-700 dark:text-indigo-100/80 font-bold">
                                            <div className="w-1 h-1 rounded-full bg-indigo-500 dark:bg-indigo-400/50" />
                                            {step}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }
    
    return (
      <div className="bg-slate-50 dark:bg-[#151b28] p-8 font-mono text-xs overflow-x-auto min-h-[200px] relative border-l-2 border-indigo-500/50 rounded-2xl shadow-xl dark:shadow-2xl">
        <pre className="text-slate-800 dark:text-indigo-400 selection:bg-indigo-500/30 relative z-10">
          {JSON.stringify(artifact.content, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div className="animate-fade-in h-full flex flex-col">
      <div className="flex items-center justify-between mb-4 mt-3 px-2 shrink-0">
        <div className="flex items-center gap-2">
           <div className="text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
             {artifact.type === 'PRD' ? <FileText size={14} /> : artifact.type === 'PLAN' ? <Map size={14} /> : <Terminal size={14} />}
           </div>
           <h4 className="text-[10px] font-bold text-slate-500 dark:text-indigo-300 uppercase tracking-[0.2em] leading-none pt-0.5">{artifact.title}</h4>
        </div>
        <button 
          onClick={() => navigator.clipboard.writeText(JSON.stringify(artifact.content, null, 2))}
          className="flex items-center gap-2 text-[10px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-white transition-all uppercase tracking-widest cursor-pointer group"
        >
          <Copy size={12} className="group-hover:scale-110 transition-transform" />
          <span className="hidden sm:inline">Copy Artifact</span>
        </button>
      </div>
      <div className="border border-slate-200 dark:border-white/10 rounded-3xl overflow-hidden shadow-2xl bg-white dark:bg-[#080a0f] flex-1">
        {renderContent()}
      </div>
    </div>
  );
};

export default ArtifactViewer;
