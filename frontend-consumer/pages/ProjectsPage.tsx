import React, { useMemo, useState } from 'react';
import { ArrowRight, LayoutDashboard, MonitorSmartphone, Settings2, ShoppingBag, Sparkles, UserSquare2 } from 'lucide-react';
import { getLang, t } from '../i18n';
import { Project } from '../types';

interface ProjectsPageProps {
  projects: Project[];
  hasSession: boolean;
  onCreateProject: (name: string, description: string) => Promise<void> | void;
  onSelectProject: (id: string) => void;
  onOpenSettings: () => void;
}

const ProjectsPage: React.FC<ProjectsPageProps> = ({
  projects,
  hasSession,
  onCreateProject,
  onSelectProject,
  onOpenSettings,
}) => {
  const [prompt, setPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const lang = getLang();

  const suggestions = useMemo(
    () => [
      { icon: MonitorSmartphone, label: t(lang, 'suggestionLanding'), prompt: t(lang, 'suggestionLandingPrompt') },
      { icon: UserSquare2, label: t(lang, 'suggestionPortfolio'), prompt: t(lang, 'suggestionPortfolioPrompt') },
      { icon: LayoutDashboard, label: t(lang, 'suggestionDashboard'), prompt: t(lang, 'suggestionDashboardPrompt') },
      { icon: ShoppingBag, label: t(lang, 'suggestionStore'), prompt: t(lang, 'suggestionStorePrompt') },
    ],
    [lang]
  );

  const recentProjects = useMemo(() => projects.slice(0, 6), [projects]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!prompt.trim() || isSubmitting || !hasSession) return;

    const name = prompt
      .trim()
      .split(/\s+/)
      .slice(0, 4)
      .join(' ');

    try {
      setIsSubmitting(true);
      await onCreateProject(name || 'Untitled App', prompt.trim());
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative h-full overflow-y-auto bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.95),_rgba(244,247,255,0.92)_42%,_rgba(236,242,255,0.85)_100%)] px-4 pb-16 pt-4 dark:bg-[radial-gradient(circle_at_top,_rgba(17,24,39,0.96),_rgba(15,23,42,0.96)_45%,_rgba(2,6,23,0.98)_100%)] sm:px-6 lg:px-10">
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(15,23,42,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.04)_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:linear-gradient(to_bottom,black_25%,transparent_100%)] dark:bg-[linear-gradient(to_right,rgba(148,163,184,0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgba(148,163,184,0.08)_1px,transparent_1px)]" />

      <div className="relative mx-auto flex min-h-full w-full max-w-6xl flex-col">
        <header className="flex items-center justify-between py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg shadow-slate-950/10 dark:bg-white dark:text-slate-950">
              <Sparkles size={18} />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-950 dark:text-white">Archon</div>
              <div className="text-xs text-slate-500 dark:text-slate-300/70">Build apps with AI</div>
            </div>
          </div>

          <button
            type="button"
            onClick={onOpenSettings}
            className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm shadow-slate-200/60 transition hover:bg-white dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10"
          >
            <Settings2 size={16} />
            {t(lang, 'settings')}
          </button>
        </header>

        <section className="flex flex-1 flex-col justify-center py-10 sm:py-16">
          <div className="mx-auto w-full max-w-4xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white/80 px-4 py-2 text-xs font-medium uppercase tracking-[0.2em] text-slate-600 shadow-sm shadow-slate-200/60 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
              <Sparkles size={14} />
              {t(lang, 'appName')}
            </div>

            <h1 className="mt-8 text-balance text-4xl font-semibold tracking-tight text-slate-950 dark:text-white sm:text-5xl lg:text-6xl">
              {t(lang, 'whatCanIBuild')}
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-balance text-base leading-7 text-slate-600 dark:text-slate-200/80 sm:text-lg">
              {t(lang, 'heroSubtitle')}
            </p>
          </div>

          <div className="mx-auto mt-8 flex w-full max-w-4xl flex-wrap justify-center gap-3">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion.label}
                type="button"
                onClick={() => setPrompt(suggestion.prompt)}
                className="inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/85 px-4 py-2 text-sm font-medium text-slate-600 shadow-sm shadow-slate-200/60 transition hover:-translate-y-0.5 hover:border-slate-200 hover:bg-white hover:text-slate-950 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10 dark:hover:text-white"
              >
                <suggestion.icon size={15} />
                {suggestion.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="mx-auto mt-8 w-full max-w-4xl">
            <div className="overflow-hidden rounded-[2rem] border border-white/80 bg-white/90 shadow-[0_30px_80px_rgba(15,23,42,0.08)] backdrop-blur dark:border-white/10 dark:bg-white/5">
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder={t(lang, 'promptPlaceholder')}
                className="min-h-[220px] w-full resize-none border-0 bg-transparent px-5 pb-5 pt-6 text-base leading-7 text-slate-950 outline-none placeholder:text-slate-400 focus:ring-0 dark:text-white dark:placeholder:text-slate-400/70 sm:min-h-[240px] sm:px-7 sm:text-lg"
              />

              <div className="flex flex-col gap-4 border-t border-slate-200/80 px-5 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-7 dark:border-white/10">
                <p className="text-sm text-slate-500 dark:text-slate-300/70">{t(lang, 'heroHint')}</p>
                <button
                  type="submit"
                  disabled={!prompt.trim() || isSubmitting || !hasSession}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-950 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-100 sm:px-6"
                >
                  {isSubmitting ? t(lang, 'sending') : t(lang, 'startBuilding')}
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          </form>

          {!hasSession && (
            <div className="mx-auto mt-4 w-full max-w-4xl rounded-[1.5rem] border border-amber-200 bg-amber-50 px-5 py-4 text-left shadow-sm shadow-amber-100/70 dark:border-amber-500/20 dark:bg-amber-500/10">
              <div className="text-sm font-semibold text-amber-900 dark:text-amber-100">{t(lang, 'authRequiredTitle')}</div>
              <div className="mt-1 text-sm leading-6 text-amber-800 dark:text-amber-100/80">{t(lang, 'authRequiredBody')}</div>
            </div>
          )}

          <section className="mx-auto mt-12 w-full max-w-5xl">
            <div className="mb-5 flex items-end justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-slate-950 dark:text-white">{t(lang, 'recentProjects')}</h2>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-300/70">{t(lang, 'recentProjectsSubtitle')}</p>
              </div>
            </div>

            {recentProjects.length > 0 ? (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {recentProjects.map((project) => (
                  <button
                    key={project.id}
                    type="button"
                    onClick={() => onSelectProject(project.id)}
                    className="group rounded-[1.75rem] border border-white/80 bg-white/85 p-5 text-left shadow-sm shadow-slate-200/60 transition hover:-translate-y-1 hover:bg-white dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="truncate text-base font-semibold text-slate-950 dark:text-white">{project.name}</div>
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                          project.status === 'RUNNING'
                            ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300'
                            : project.status === 'COMPLETED'
                            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300'
                            : project.status === 'FAILED'
                            ? 'bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300'
                            : 'bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300'
                        }`}
                      >
                        {project.status === 'COMPLETED'
                          ? t(lang, 'statusCompleted')
                          : project.status === 'FAILED'
                          ? t(lang, 'statusFailed')
                          : project.status === 'RUNNING'
                          ? t(lang, 'statusRunning')
                          : t(lang, 'statusIdle')}
                      </span>
                    </div>
                    <p className="mt-3 line-clamp-3 text-sm leading-6 text-slate-500 dark:text-slate-300/70">
                      {project.description}
                    </p>
                    <div className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-slate-700 transition group-hover:text-slate-950 dark:text-slate-200 dark:group-hover:text-white">
                      {t(lang, 'openProject')}
                      <ArrowRight size={15} />
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="rounded-[1.75rem] border border-dashed border-slate-300 bg-white/75 px-6 py-10 text-center text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-300/70">
                {t(lang, 'noProjectsYet')}
              </div>
            )}
          </section>
        </section>
      </div>
    </div>
  );
};

export default ProjectsPage;
