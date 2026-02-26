
import React, { useState } from 'react';
import { SystemSettings } from '../types';
import { 
  X, Moon, Sun, Cpu, User, Lock, Brain, Check, 
  ExternalLink, Volume2, Shield, Info, Sparkles 
} from 'lucide-react';

interface SettingsModalProps {
  settings: SystemSettings;
  onUpdate: (updates: Partial<SystemSettings>) => void;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ settings, onUpdate, onClose }) => {
  const [localSettings, setLocalSettings] = useState<SystemSettings>({ ...settings });
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleApply = () => {
    onUpdate(localSettings);
    onClose();
  };

  const handleBackdropMouseDown = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const sectionClasses = "p-4 md:p-6 rounded-3xl border border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-white/[0.02] space-y-4";
  const labelClasses = "text-xs font-black text-slate-900 dark:text-white flex items-center gap-2";
  const subLabelClasses = "text-[11px] text-slate-500 dark:text-slate-400 font-bold leading-relaxed";
  const inputClasses = "w-full bg-white dark:bg-black/20 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-2.5 text-[11px] text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition-colors font-bold";

  return (
    <div 
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 bg-black/70 backdrop-blur-sm animate-fade-in"
      onMouseDown={handleBackdropMouseDown}
    >
      <div 
        className="bg-white dark:bg-[#0d1017] border border-slate-200 dark:border-white/10 w-full max-w-2xl rounded-3xl md:rounded-[2.5rem] overflow-hidden shadow-2xl flex flex-col animate-fade-in-up max-h-[90vh] sm:max-h-[85vh]"
        onMouseDown={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-5 md:p-8 border-b border-slate-200 dark:border-white/5 flex items-center justify-between shrink-0">
          <div>
            <h2 className="text-lg md:text-xl font-black text-slate-900 dark:text-white tracking-tight uppercase">Settings</h2>
            <p className="text-[10px] text-slate-400 dark:text-indigo-400/40 font-black uppercase tracking-[0.2em] mt-1">Personalize how you interact with ai-dev-team</p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-slate-100 dark:hover:bg-white/5 rounded-xl transition-colors text-slate-400 cursor-pointer"
          >
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-5 md:p-8 space-y-6 md:space-y-8 custom-scrollbar">
          
          {/* Vibe Coding Level */}
          <div className={sectionClasses}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-black text-slate-900 dark:text-white">Vibe coding level</span>
                <span className="px-1.5 py-0.5 rounded-md bg-indigo-600/10 text-indigo-600 dark:text-indigo-400 text-[8px] font-black uppercase border border-indigo-500/20">Beta</span>
              </div>
            </div>
            <p className={subLabelClasses}>Showcase your vibe coding momentum and progress.</p>
            <div className="space-y-3">
              <div className="w-full h-1.5 bg-slate-200 dark:bg-white/10 rounded-full overflow-hidden">
                <div className="h-full bg-indigo-500 w-[65%] shadow-[0_0_10px_rgba(99,102,241,0.5)]"></div>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] font-black text-slate-500 dark:text-indigo-300">
                L3: Gold <Info size={10} className="opacity-50" />
              </div>
            </div>
          </div>

          {/* AI Reasoning Engine */}
          <div className="space-y-4">
             <label className="text-[10px] font-black text-indigo-600 dark:text-indigo-500 uppercase tracking-[0.2em] flex items-center gap-2">
               <Brain size={12} />
               Reasoning Engine
             </label>
             <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
               {[
                 { id: 'Gemini 3 Pro', desc: 'Complex reasoning.' },
                 { id: 'Claude Opus 4.6', desc: 'Advanced logic.' },
                 { id: 'Chatgpt-5.2', desc: 'Optimized code.' }
               ].map((m) => (
                 <button
                   key={m.id}
                   onClick={() => setLocalSettings({ ...localSettings, model: m.id as any })}
                   className={`flex flex-col p-4 rounded-2xl border-2 text-left transition-colors relative group cursor-pointer ${
                     localSettings.model === m.id 
                     ? 'bg-indigo-600 text-white border-indigo-500 shadow-lg shadow-indigo-600/10' 
                     : 'bg-slate-50 dark:bg-white/5 border-slate-200 dark:border-white/5 hover:border-indigo-500/30 text-slate-500 dark:text-slate-400'
                   }`}
                 >
                   <div className="flex justify-between items-start w-full mb-1">
                     <span className="text-[10px] font-black uppercase tracking-tight">{m.id}</span>
                     {localSettings.model === m.id && (
                       <div className="bg-white/20 p-0.5 rounded-full shadow-sm flex items-center justify-center">
                         <Check size={10} className="text-white" strokeWidth={4} />
                       </div>
                     )}
                   </div>
                   <span className={`text-[9px] font-bold leading-tight transition-colors ${localSettings.model === m.id ? 'text-white/70' : 'text-slate-400 dark:text-slate-500'}`}>
                     {m.desc}
                   </span>
                 </button>
               ))}
             </div>
          </div>

          {/* Profile Section */}
          <div className={sectionClasses}>
            <div className="flex items-center justify-between">
              <span className={labelClasses}>Profile</span>
              <button className="text-[10px] font-black text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 cursor-pointer">
                Open profile on ai-dev-team.app/{localSettings.username}
                <ExternalLink size={10} />
              </button>
            </div>
            <p className={subLabelClasses}>Change name, location, avatar, and banner on your profile.</p>
            
            <div className="space-y-6 pt-4 border-t border-slate-200 dark:border-white/5">
              <div className="grid grid-cols-1 md:grid-cols-[1fr,auto] gap-4 items-end">
                <div className="space-y-2">
                  <label className="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Username</label>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500 font-bold mb-1">Your public identifier and profile URL.</p>
                  <input 
                    type="text" 
                    value={localSettings.username}
                    onChange={(e) => setLocalSettings({...localSettings, username: e.target.value})}
                    className={inputClasses} 
                  />
                </div>
                <button className="bg-slate-900 dark:bg-white text-white dark:text-black px-4 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:brightness-110 active:scale-95 transition-all cursor-pointer">Update</button>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Email</label>
                <p className="text-[10px] text-slate-400 dark:text-slate-500 font-bold mb-1">Your email address associated with your account.</p>
                <input 
                  type="email" 
                  value={localSettings.email}
                  onChange={(e) => setLocalSettings({...localSettings, email: e.target.value})}
                  className={inputClasses} 
                />
              </div>
            </div>
          </div>

          {/* Chat Settings */}
          <div className={sectionClasses}>
            <div className="flex items-center justify-between gap-4">
               <div className="space-y-1">
                  <span className={labelClasses}>Chat suggestions</span>
                  <p className={subLabelClasses}>Show helpful suggestions in the chat interface to enhance your experience.</p>
               </div>
               <button 
                  onClick={() => setLocalSettings({...localSettings, chatSuggestions: !localSettings.chatSuggestions})}
                  className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none cursor-pointer ${localSettings.chatSuggestions ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-white/10'}`}
               >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${localSettings.chatSuggestions ? 'translate-x-6' : 'translate-x-1'}`} />
               </button>
            </div>

            <div className="pt-6 border-t border-slate-200 dark:border-white/5 space-y-4">
              <div className="space-y-1">
                <span className={labelClasses}>Generation complete sound</span>
                <p className={subLabelClasses}>Plays a satisfying sound notification when a generation is finished.</p>
              </div>
              
              <div className="space-y-3">
                {[
                  { id: 'first', label: 'First generation', icon: Volume2 },
                  { id: 'always', label: 'Always', icon: Volume2 },
                  { id: 'never', label: 'Never', icon: Moon }
                ].map((opt) => (
                  <label key={opt.id} className="flex items-center gap-3 cursor-pointer group">
                    <input 
                      type="radio"
                      name="sound"
                      checked={localSettings.completionSound === opt.id}
                      onChange={() => setLocalSettings({...localSettings, completionSound: opt.id as any})}
                      className="w-4 h-4 border-2 border-slate-300 dark:border-white/20 text-indigo-600 focus:ring-indigo-500 bg-transparent cursor-pointer"
                    />
                    <div className="flex items-center gap-2">
                      <opt.icon size={14} className="text-slate-400 group-hover:text-indigo-500 transition-colors" />
                      <span className="text-[11px] font-bold text-slate-700 dark:text-slate-200">{opt.label}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Account Security */}
          <div className={sectionClasses}>
            <div className="flex items-center gap-2 mb-2">
              <Shield size={14} className="text-indigo-500" />
              <span className={labelClasses}>Account Security</span>
            </div>
            <p className={subLabelClasses}>Ensure your account remains private with a strong password.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <input 
                type="password" 
                placeholder="New password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={inputClasses} 
              />
              <input 
                type="password" 
                placeholder="Confirm password" 
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={inputClasses} 
              />
            </div>
          </div>

        </div>

        {/* Action Footer */}
        <div className="p-5 md:p-8 border-t border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-white/[0.01] flex flex-col sm:flex-row items-center justify-between gap-4 shrink-0">
          <p className="text-[10px] text-slate-400 font-black uppercase tracking-widest text-center sm:text-left">Settings automatically persist to session</p>
          <button 
            onClick={handleApply}
            className="w-full sm:w-auto px-10 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl text-xs font-black uppercase tracking-widest shadow-xl shadow-indigo-600/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Check size={16} />
            Apply & Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
