import React from 'react';
import { Project } from '../types';
import { Clock, CheckCircle, AlertCircle, PlayCircle, ArrowRight, Zap } from 'lucide-react';

interface ProjectCardProps {
  project: Project;
  onClick: () => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onClick }) => {
  const getStatusColor = () => {
    switch (project.status) {
      case 'RUNNING': return 'text-primary bg-primary/10 border-primary/20 shadow-[0_0_10px_rgba(59,130,246,0.1)]';
      case 'COMPLETED': return 'text-accent bg-accent/10 border-accent/20';
      case 'FAILED': return 'text-danger bg-danger/10 border-danger/20';
      default: return 'text-slate-400 bg-slate-800/30 border-slate-700/30';
    }
  };

  const StatusIcon = () => {
    switch (project.status) {
      case 'RUNNING': return <Clock className="w-3.5 h-3.5 animate-spin" />;
      case 'COMPLETED': return <CheckCircle className="w-3.5 h-3.5" />;
      case 'FAILED': return <AlertCircle className="w-3.5 h-3.5" />;
      default: return <PlayCircle className="w-3.5 h-3.5" />;
    }
  };

  return (
    <div 
      onClick={onClick}
      className="group relative flex flex-col p-6 rounded-2xl border border-white/5 bg-surface/50 backdrop-blur-sm hover:bg-surface transition-all duration-500 cursor-pointer overflow-hidden hover:border-primary/50 hover:shadow-[0_0_30px_rgba(59,130,246,0.15)]"
    >
      {/* Gradient Blob for Glow Effect */}
      <div className="absolute -top-20 -right-20 w-40 h-40 bg-primary/10 rounded-full blur-3xl group-hover:bg-primary/20 transition-all duration-500"></div>

      <div className="relative z-10 flex justify-between items-start mb-4">
        <h3 className="text-lg font-bold text-white tracking-tight pr-4 group-hover:text-primary transition-colors">
          {project.name}
        </h3>
        <div className={`px-2.5 py-1 rounded-full text-[10px] uppercase tracking-wider font-bold border flex items-center gap-1.5 ${getStatusColor()}`}>
          <StatusIcon />
          <span>{project.status}</span>
        </div>
      </div>
      
      <p className="relative z-10 text-slate-400 text-sm leading-relaxed line-clamp-2 mb-8 flex-1 group-hover:text-slate-300 transition-colors">
        {project.description}
      </p>

      <div className="relative z-10 flex items-center justify-between pt-4 border-t border-white/5">
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold mb-0.5">Current Stage</span>
          <span className="text-xs text-indigo-300 font-medium capitalize flex items-center gap-1.5">
            {project.currentStage === 'idle' ? <span className="w-1.5 h-1.5 rounded-full bg-slate-600"></span> : <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>}
            {project.currentStage}
          </span>
        </div>
        
        <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-slate-400 group-hover:bg-primary group-hover:text-white transition-all transform group-hover:translate-x-1">
          <ArrowRight size={14} />
        </div>
      </div>
    </div>
  );
};

export default ProjectCard;