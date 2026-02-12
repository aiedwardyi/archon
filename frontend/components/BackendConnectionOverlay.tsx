
import React, { useState } from 'react';
import { RefreshCw, ServerOff, Terminal as TerminalIcon, X } from 'lucide-react';
import { backend } from '../services/orchestrator';

interface BackendConnectionOverlayProps {
  onClose: () => void;
}

const BackendConnectionOverlay: React.FC<BackendConnectionOverlayProps> = ({ onClose }) => {
  const [isRetrying, setIsRetrying] = useState(false);

  const handleRetry = async () => {
    setIsRetrying(true);
    await backend.retryConnection();
    // Simulate a brief delay for UX
    setTimeout(() => setIsRetrying(false), 800);
  };

  return (
    <div className="fixed inset-0 z-[1000] flex items-center justify-center bg-[#080a0f]/90 backdrop-blur-md p-4 overflow-y-auto animate-fade-in">
      {/* Background Glow */}
      <div className="absolute inset-0 bg-grid-pattern opacity-5 pointer-events-none"></div>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-red-500/5 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-[440px] bg-[#0b0e14] border border-red-500/20 rounded-[2rem] md:rounded-[2.5rem] shadow-2xl p-6 md:p-10 relative overflow-hidden flex flex-col items-center text-center gap-6 md:gap-8 my-auto">
        
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-6 right-6 p-2 rounded-full hover:bg-white/5 text-slate-500 hover:text-white transition-all cursor-pointer z-20 group"
          title="Dismiss"
        >
          <X size={20} className="group-hover:rotate-90 transition-transform duration-300" />
        </button>

        {/* Disconnected Icon */}
        <div className="relative group shrink-0 mt-4">
          <div className="absolute -inset-4 bg-red-500/10 rounded-full blur-xl group-hover:bg-red-500/20 transition-all duration-700"></div>
          <div className="w-20 h-20 md:w-24 md:h-24 bg-red-500/10 border border-red-500/20 rounded-2xl md:rounded-3xl flex items-center justify-center text-red-500 relative z-10 shadow-lg shadow-red-500/10">
            <ServerOff size={36} className="md:w-[44px] md:h-[44px]" />
          </div>
        </div>

        {/* Content */}
        <div className="space-y-3 md:space-y-5">
          <h1 className="text-2xl md:text-3xl font-black text-white tracking-tighter uppercase leading-none">
            Backend Required
          </h1>
          <div className="text-[12px] md:text-[13px] text-slate-400 font-bold leading-relaxed max-w-[340px] mx-auto space-y-1">
            <p>The Flask server is not connected. To use the Multi-Agent Platform, please start the backend at</p>
            <p className="text-red-500 font-black text-sm md:text-base">http://localhost:5000</p>
          </div>
        </div>

        {/* Setup Instructions Block */}
        <div className="w-full bg-black/40 border border-white/5 rounded-[1.25rem] md:rounded-[1.5rem] p-5 md:p-6 text-left relative group">
          <div className="flex items-center gap-2 mb-4 md:mb-6 text-[9px] md:text-[10px] font-black text-slate-500 uppercase tracking-widest border-b border-white/5 pb-3 md:pb-4">
            <TerminalIcon size={12} className="text-slate-600" />
            _ SETUP INSTRUCTIONS
          </div>
          
          <div className="font-mono text-[10px] md:text-[11px] leading-relaxed space-y-3">
            <div className="flex gap-2 md:gap-3">
              <span className="text-slate-700 shrink-0">1.</span>
              <span className="text-slate-400 break-all">cd ai-dev-team</span>
            </div>
            <div className="flex gap-2 md:gap-3">
              <span className="text-slate-700 shrink-0">2.</span>
              <span className="text-slate-400 break-all">pip install -r requirements.txt</span>
            </div>
            <div className="flex gap-2 md:gap-3">
              <span className="text-slate-700 shrink-0">3.</span>
              <span className="text-slate-400 break-all">.\venv\Scripts\Activate</span>
            </div>
            <div className="flex gap-2 md:gap-3">
              <span className="text-slate-700 shrink-0">4.</span>
              <span className="text-slate-400 break-all">$env:OPENAI_API_KEY = "your_key"</span>
            </div>
            <div className="flex gap-2 md:gap-3">
              <span className="text-slate-700 shrink-0">5.</span>
              <span className="text-slate-400 break-all">$env:GENAI_API_KEY = "your_key"</span>
            </div>
            <div className="flex gap-2 md:gap-3">
              <span className="text-slate-700 shrink-0">6.</span>
              <span className="text-slate-400 break-all">python backend/app.py</span>
            </div>
          </div>
        </div>

        {/* Action */}
        <button 
          onClick={handleRetry}
          disabled={isRetrying}
          className="w-full bg-white text-black py-4 md:py-5 rounded-xl md:rounded-2xl font-black text-[11px] md:text-xs uppercase tracking-[0.2em] shadow-xl hover:bg-slate-100 active:scale-[0.98] transition-all flex items-center justify-center gap-3 group cursor-pointer shrink-0"
        >
          <RefreshCw size={16} className={`${isRetrying ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-700'}`} />
          {isRetrying ? 'RECONNECTING...' : 'RETRY CONNECTION'}
        </button>

      </div>
    </div>
  );
};

export default BackendConnectionOverlay;
