import React from 'react';
import { CheckCircle2, Clock3, Map } from 'lucide-react';
import { Artifact, PlanResponse } from '../types';

interface ArtifactViewerProps {
  artifact: Artifact;
}

const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact }) => {
  if (artifact.type !== 'PLAN') {
    return (
      <div className="rounded-[2rem] border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm dark:border-white/10 dark:bg-[#111827] dark:text-slate-300">
        This view is only used for build plans.
      </div>
    );
  }

  const plan = artifact.content as PlanResponse;

  return (
    <div className="rounded-[2rem] border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#111827]">
      <div className="border-b border-slate-200 px-6 py-5 dark:border-white/10">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-white dark:bg-white dark:text-slate-950">
            <Map size={18} />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-semibold tracking-tight text-slate-950 dark:text-white">{artifact.title}</h3>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-300/70">
              A simple rollout view of what Archon is building next.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
            <Clock3 size={14} />
            {plan.estimatedTimeline}
          </div>
        </div>
      </div>

      <div className="space-y-5 p-6">
        {plan.phases.map((phase, index) => (
          <section
            key={`${phase.name}-${index}`}
            className="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-white/5"
          >
            <div className="flex flex-wrap items-start gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-white text-slate-950 shadow-sm dark:bg-slate-950 dark:text-white">
                <span className="text-sm font-semibold">{index + 1}</span>
              </div>
              <div className="min-w-0 flex-1">
                <h4 className="text-base font-semibold text-slate-950 dark:text-white">{phase.name}</h4>
                {phase.description && (
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-300/70">{phase.description}</p>
                )}
              </div>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {phase.steps.map((step) => (
                <div
                  key={step}
                  className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 dark:border-white/10 dark:bg-slate-950/40 dark:text-slate-100"
                >
                  <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-emerald-500" />
                  <span>{step}</span>
                </div>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
};

export default ArtifactViewer;
