import React from 'react';
import { AgentStage } from '../types';
import { Check, Sparkles } from 'lucide-react';

interface StageStepperProps {
  currentStage: AgentStage;
}

const steps = [
  { id: 'pm', label: 'PM Agent' },
  { id: 'planner', label: 'Planner' },
  { id: 'engineer', label: 'Engineer' },
];

const StageStepper: React.FC<StageStepperProps> = ({ currentStage }) => {
  const getStepStatus = (stepId: string) => {
    const stages = ['idle', 'pm', 'planner', 'engineer', 'complete'];
    const currentIndex = stages.indexOf(currentStage);
    const stepIndex = stages.indexOf(stepId);

    if (currentStage === 'complete') return 'completed';
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <div className="w-full py-8">
      <div className="flex items-center justify-between relative max-w-3xl mx-auto px-4">
        {/* Background Track */}
        <div className="absolute top-1/2 left-0 w-full h-[2px] bg-white/5 -z-0 rounded-full"></div>
        
        {/* Progress Fill - Gradient Blue to Purple */}
        <div className={`absolute top-1/2 left-0 h-[2px] bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 -z-0 rounded-full transition-all duration-1000 ease-out shadow-[0_0_15px_rgba(99,102,241,0.4)] ${
           currentStage === 'pm' ? 'w-[15%]' : 
           currentStage === 'planner' ? 'w-[50%]' : 
           currentStage === 'engineer' ? 'w-[85%]' : 
           currentStage === 'complete' ? 'w-full' : 'w-0'
        }`}></div>
        
        {steps.map((step, idx) => {
          const status = getStepStatus(step.id);
          const isActive = status === 'active';
          
          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center gap-4 group">
              <div 
                className={`
                  relative w-14 h-14 rounded-full flex items-center justify-center border-2 transition-all duration-700 ease-in-out bg-[#0b0e14]
                  ${status === 'completed' || status === 'active' 
                    ? 'border-transparent bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-[0_0_25px_rgba(59,130,246,0.3)]' 
                    : 'border-white/10 text-white/20'
                  }
                  ${isActive ? 'scale-110 shadow-[0_0_40px_rgba(59,130,246,0.5)]' : 'scale-100'}
                `}
              >
                {/* Active Pulse Rings */}
                {isActive && (
                  <>
                    <div className="absolute inset-0 rounded-full bg-blue-500/20 animate-ping opacity-75"></div>
                    <div className="absolute -inset-2 rounded-full border border-blue-500/10 animate-pulse"></div>
                  </>
                )}

                {/* Inner Circle to simulate ring effect */}
                <div className={`
                  w-12 h-12 rounded-full flex items-center justify-center bg-[#0b0e14] transition-all duration-300 
                  ${isActive ? 'scale-90 border border-blue-500/20' : 'scale-100'}
                `}>
                    {status === 'completed' ? (
                        <Check size={20} className="text-blue-400 drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]" />
                    ) : isActive ? (
                        <div className="relative">
                          <div className="w-3.5 h-3.5 rounded-full bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,1)]"></div>
                          <div className="absolute -top-1 -right-1">
                            <Sparkles size={8} className="text-white animate-pulse" />
                          </div>
                        </div>
                    ) : (
                        <div className="w-2 h-2 rounded-full bg-white/10"></div>
                    )}
                </div>
              </div>
              
              <div className="flex flex-col items-center gap-1">
                <span className={`text-[10px] font-black uppercase tracking-[0.25em] transition-all duration-500 ${
                  isActive ? 'text-blue-400 drop-shadow-[0_0_10px_rgba(59,130,246,0.6)] translate-y-[-2px]' : 
                  status === 'completed' ? 'text-indigo-300/80' : 'text-slate-600'
                }`}>
                  {step.label}
                </span>
                {isActive && (
                  <div className="h-1 w-4 bg-blue-500/40 rounded-full animate-pulse"></div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StageStepper;