
import React, { useState } from 'react';
import { Sparkles, Send, Zap, ArrowRight, Github, Layout, Activity, Database, Shield, Rocket, Smartphone } from 'lucide-react';

interface ProjectsPageProps {
  onCreateProject: (name: string, description: string) => void;
  onSelectProject: (id: string) => void;
}

const suggestions = [
  { label: 'SaaS Dashboard', icon: Layout, prompt: 'Build a modern SaaS dashboard with a sidebar, dark mode, and real-time revenue charts.' },
  { label: 'Fitness Tracker', icon: Activity, prompt: 'Create a fitness tracking app that allows users to log workouts and visualize progress over time.' },
  { label: 'AI Features', icon: Sparkles, prompt: 'Add AI-powered insights and automated data analysis to a standard CRM platform.' },
  { label: 'Mobile App', icon: Smartphone, prompt: 'Design a responsive mobile-first application for a local food delivery service.' },
];

const ProjectsPage: React.FC<ProjectsPageProps> = ({ onCreateProject }) => {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    
    const name = prompt.split(' ').slice(0, 3).join(' ') || "Untitled App";
    onCreateProject(name, prompt);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 md:p-8 relative transition-colors duration-300 overflow-y-auto">
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.1] animate-grid-move pointer-events-none"></div>
      
      <div className="w-full max-w-2xl relative z-10 animate-fade-in py-10 md:py-0">
        <div className="text-center mb-8 md:mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400 text-[10px] font-bold uppercase tracking-widest mb-6 animate-pulse-glow">
            < Zap size={10} fill="currentColor" />
            Next-Gen Multi-Agent Swarm
          </div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-black text-slate-900 dark:text-white tracking-tighter mb-4 leading-none">
            What can I <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-400 dark:from-indigo-400 dark:via-violet-400 dark:to-teal-400 animate-text-glow">build</span> for you?
          </h1>
          <p className="text-slate-500 dark:text-indigo-200/60 text-base md:text-lg font-bold px-4 md:px-0">
            Describe your application. Our agent swarm handles the PRD, Architecture, and Code.
          </p>
        </div>

        {/* Suggestion Chips */}
        <div className="mb-6 flex flex-wrap gap-2 justify-center animate-fade-in px-2">
          {suggestions.map((item, idx) => (
            <button 
              key={idx}
              onClick={() => setPrompt(item.prompt)}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-slate-100 dark:bg-white/[0.04] border border-slate-200 dark:border-white/10 text-slate-600 dark:text-indigo-100/70 hover:text-indigo-600 dark:hover:text-white hover:bg-indigo-50 dark:hover:bg-white/10 hover:border-indigo-500/50 transition-all text-xs font-bold whitespace-nowrap group cursor-pointer shadow-lg shadow-black/5"
            >
              <item.icon size={13} className="text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform" />
              {item.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="relative group animate-fade-in px-2">
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-600 via-violet-600 to-teal-600 rounded-3xl blur opacity-10 group-focus-within:opacity-30 transition duration-1000"></div>
          
          <div className="relative bg-white dark:bg-[#0d1017]/95 backdrop-blur-3xl border border-slate-200 dark:border-white/15 rounded-3xl p-2 shadow-2xl overflow-hidden">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe your project in detail..."
              className="w-full bg-transparent border-none text-slate-900 dark:text-white px-4 md:px-6 pt-4 md:pt-6 pb-20 focus:ring-0 focus:outline-none outline-none resize-none min-h-[160px] md:min-h-[180px] text-base md:text-lg font-bold placeholder:text-slate-300 dark:placeholder:text-slate-500 custom-scrollbar"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
            />
            
            <div className="absolute bottom-4 left-6 right-4 flex items-center justify-between">
              <span className="text-[10px] text-indigo-600/50 dark:text-indigo-400/50 font-mono hidden md:block uppercase tracking-widest font-black">Press ↵ to launch pipeline</span>
              <button 
                type="submit"
                disabled={!prompt.trim()}
                className="flex items-center gap-2 bg-gradient-to-br from-indigo-600 to-violet-600 hover:brightness-110 disabled:opacity-30 text-white px-6 py-3 rounded-2xl font-black transition-all shadow-lg shadow-indigo-500/30 group/btn cursor-pointer disabled:cursor-not-allowed w-full md:w-auto justify-center"
              >
                <span>Generate</span>
                <Send size={18} className="group-hover/btn:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        </form>
      </div>

      <div className="md:absolute bottom-8 md:bottom-12 left-0 right-0 flex justify-center items-center gap-8 text-slate-400 dark:text-slate-500 mt-8 md:mt-0">
        <div className="flex items-center gap-2 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors cursor-default group">
          <Github size={16} className="group-hover:scale-110 transition-transform" />
          <span className="text-xs font-black uppercase tracking-widest">Source</span>
        </div>
        <div className="h-4 w-[1px] bg-slate-200 dark:bg-white/10"></div>
        <div className="flex items-center gap-2 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors cursor-default group">
          <Sparkles size={16} className="group-hover:scale-110 transition-transform" />
          <span className="text-xs font-black uppercase tracking-widest">Pro Features</span>
        </div>
      </div>
    </div>
  );
};

export default ProjectsPage;
