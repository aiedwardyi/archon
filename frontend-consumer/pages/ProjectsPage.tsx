import React, { useMemo, useState } from 'react';
import {
  ArrowRight,
  LayoutDashboard,
  MonitorSmartphone,
  Settings2,
  Sparkles,
  UserSquare2,
} from 'lucide-react';
import SessionMenu from '../components/SessionMenu';
import { t, type Lang } from '../i18n';
import { getPreviewUrl } from '../services/orchestrator';
import { AuthUser } from '../services/auth';
import { Project } from '../types';

interface ProjectsPageProps {
  lang: Lang;
  projects: Project[];
  hasSession: boolean;
  authUser: AuthUser | null;
  onCreateProject: (name: string, description: string) => Promise<void> | void;
  onSelectProject: (id: string) => void;
  onOpenSettings: () => void;
  onNavigate: (href: string) => void;
  onSignOut: () => Promise<void> | void;
}

function getStatusAccent(status: Project['status']) {
  if (status === 'RUNNING') return '#f59e0b';
  if (status === 'COMPLETED') return '#10b981';
  if (status === 'FAILED') return '#fb7185';
  return '#64748b';
}

const ProjectsPage: React.FC<ProjectsPageProps> = ({
  lang,
  projects,
  hasSession,
  authUser,
  onCreateProject,
  onSelectProject,
  onOpenSettings,
  onNavigate,
  onSignOut,
}) => {
  const [prompt, setPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const inspirationCards = useMemo(
    () => [
      {
        icon: MonitorSmartphone,
        title: t(lang, 'suggestionLanding'),
        prompt: t(lang, 'suggestionLandingPrompt'),
      },
      {
        icon: UserSquare2,
        title: t(lang, 'suggestionPortfolio'),
        prompt: t(lang, 'suggestionPortfolioPrompt'),
      },
      {
        icon: LayoutDashboard,
        title: t(lang, 'suggestionDashboard'),
        prompt: t(lang, 'suggestionDashboardPrompt'),
      },
    ],
    [lang]
  );

  const recentProjects = useMemo(() => projects.slice(0, 6), [projects]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!prompt.trim() || isSubmitting) return;

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
    <div className="relative h-full overflow-y-auto bg-[#03050f] text-white">
      <style>{`
        @keyframes meshDrift {
          0% { transform: translate3d(0, 0, 0) scale(1); opacity: 0.58; }
          50% { transform: translate3d(2%, -3%, 0) scale(1.08); opacity: 0.82; }
          100% { transform: translate3d(0, 0, 0) scale(1); opacity: 0.58; }
        }
        @keyframes orbFloatA {
          0% { transform: translate3d(-8%, -2%, 0) scale(1); }
          50% { transform: translate3d(6%, 5%, 0) scale(1.12); }
          100% { transform: translate3d(-8%, -2%, 0) scale(1); }
        }
        @keyframes orbFloatB {
          0% { transform: translate3d(4%, 3%, 0) scale(1.05); }
          50% { transform: translate3d(-6%, -5%, 0) scale(0.96); }
          100% { transform: translate3d(4%, 3%, 0) scale(1.05); }
        }
        @keyframes orbFloatC {
          0% { transform: translate3d(0, 0, 0) scale(1); }
          50% { transform: translate3d(-5%, 6%, 0) scale(1.1); }
          100% { transform: translate3d(0, 0, 0) scale(1); }
        }
        @keyframes headlineSweep {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        @keyframes panelPulse {
          0% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.22), 0 0 0 1px rgba(129, 140, 248, 0.25); }
          50% { box-shadow: 0 0 0 10px rgba(79, 70, 229, 0.03), 0 0 0 1px rgba(129, 140, 248, 0.6), 0 0 30px rgba(79, 70, 229, 0.28); }
          100% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.18), 0 0 0 1px rgba(129, 140, 248, 0.25); }
        }
        @keyframes cardGlow {
          0% { box-shadow: 0 20px 40px rgba(3, 5, 15, 0.4); }
          50% { box-shadow: 0 28px 80px rgba(79, 70, 229, 0.22); }
          100% { box-shadow: 0 20px 40px rgba(3, 5, 15, 0.4); }
        }
        @keyframes buttonGlow {
          0% { box-shadow: 0 16px 40px rgba(79, 70, 229, 0.3); }
          50% { box-shadow: 0 18px 55px rgba(8, 145, 178, 0.38); }
          100% { box-shadow: 0 16px 40px rgba(79, 70, 229, 0.3); }
        }
        .projects-mesh::before {
          content: '';
          position: absolute;
          inset: -15%;
          background:
            radial-gradient(circle at 18% 18%, rgba(79, 70, 229, 0.18), transparent 24%),
            radial-gradient(circle at 78% 22%, rgba(124, 58, 237, 0.16), transparent 25%),
            radial-gradient(circle at 58% 78%, rgba(8, 145, 178, 0.14), transparent 28%);
          filter: blur(24px);
          animation: meshDrift 12s ease-in-out infinite;
        }
        .hero-headline {
          background-image: linear-gradient(120deg, #ffffff 8%, #dbe4ff 28%, #8b5cf6 58%, #4f46e5 82%, #ffffff 100%);
          background-size: 220% 220%;
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
          animation: headlineSweep 4s ease-in-out infinite;
        }
        .floating-card {
          background:
            linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)),
            linear-gradient(135deg, rgba(79, 70, 229, 0.1), rgba(8, 145, 178, 0.06), rgba(124, 58, 237, 0.1));
          animation: cardGlow 8s ease-in-out infinite;
        }
        .floating-card.focused {
          animation: cardGlow 8s ease-in-out infinite, panelPulse 1.8s ease-in-out infinite;
        }
        .cta-button:hover {
          animation: buttonGlow 1.8s ease-in-out infinite;
        }
        .recent-card:hover .recent-arrow {
          opacity: 1;
          transform: translateX(0);
        }
        .recent-card:hover .recent-shell {
          border-color: rgba(129, 140, 248, 0.38);
          box-shadow: 0 18px 60px rgba(79, 70, 229, 0.18);
        }
        .inspiration-card:hover {
          transform: translateY(-8px) scale(1.01);
          box-shadow: 0 22px 70px rgba(79, 70, 229, 0.22);
          border-color: rgba(129, 140, 248, 0.36);
        }
        button, a {
          -webkit-font-smoothing: antialiased;
          backface-visibility: hidden;
          transform: translateZ(0);
        }
      `}</style>

      <div className="projects-mesh pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute left-[-12%] top-[-8%] h-[38rem] w-[38rem] rounded-full blur-[110px]"
          style={{ backgroundColor: 'rgba(79, 70, 229, 0.42)', animation: 'orbFloatA 18s ease-in-out infinite' }}
        />
        <div
          className="absolute right-[-10%] top-[10%] h-[34rem] w-[34rem] rounded-full blur-[110px]"
          style={{ backgroundColor: 'rgba(124, 58, 237, 0.34)', animation: 'orbFloatB 20s ease-in-out infinite' }}
        />
        <div
          className="absolute bottom-[-16%] left-[28%] h-[32rem] w-[32rem] rounded-full blur-[110px]"
          style={{ backgroundColor: 'rgba(8, 145, 178, 0.28)', animation: 'orbFloatC 16s ease-in-out infinite' }}
        />
      </div>

      <div className="relative mx-auto flex min-h-full w-full max-w-7xl flex-col px-4 pb-16 pt-5 sm:px-6 lg:px-10">
        <header className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-[1.4rem] border border-white/10 bg-white/5 shadow-[0_12px_40px_rgba(79,70,229,0.18)] backdrop-blur-xl">
              <Sparkles size={18} className="text-indigo-200" />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-[0.24em] text-white/90">{t(lang, 'appName')}</div>
              <div className="text-xs uppercase tracking-[0.32em] text-white/40">Consumer Studio</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <SessionMenu
              hasSession={hasSession}
              user={authUser}
              signInHref="/login"
              onNavigate={onNavigate}
              onSignOut={onSignOut}
            />
            <button
              type="button"
              onClick={onOpenSettings}
              className="inline-flex h-11 items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 text-sm font-medium text-white/80 backdrop-blur-xl transition hover:border-white/20 hover:bg-white/10 hover:text-white"
            >
              <Settings2 size={16} />
              {t(lang, 'settings')}
            </button>
          </div>
        </header>

        <section className="flex flex-1 flex-col justify-center py-12 sm:py-16 lg:py-20">
          <div className="mx-auto w-full max-w-5xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-[11px] font-medium uppercase tracking-[0.32em] text-white/65 backdrop-blur-xl">
              <Sparkles size={14} className="text-cyan-300" />
              Build apps with AI
            </div>

            <h1 className="hero-headline mt-8 text-balance text-[clamp(3.5rem,8vw,7rem)] font-semibold leading-[0.92]">
              {t(lang, 'whatCanIBuild')}
            </h1>
            <p className="mx-auto mt-5 max-w-3xl text-balance text-base leading-7 text-white/62 sm:text-lg">
              {t(lang, 'heroSubtitle')}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mx-auto mt-10 w-full max-w-5xl">
            <div
              className={`floating-card overflow-hidden rounded-[2rem] border border-white/10 backdrop-blur-2xl transition ${isFocused ? 'focused' : ''}`}
            >
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    if (prompt.trim() && !isSubmitting) {
                      event.currentTarget.form?.requestSubmit();
                    }
                  }
                }}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder={t(lang, 'promptPlaceholder')}
                className="min-h-[240px] w-full resize-none border-0 bg-transparent px-6 pb-6 pt-7 text-base leading-7 text-white outline-none placeholder:text-white/30 focus:ring-0 sm:min-h-[260px] sm:px-8 sm:text-lg"
              />

              <div className="flex flex-col gap-4 border-t border-white/10 px-6 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-8">
                <p className="text-sm text-white/46">{t(lang, 'heroHint')}</p>
                <button
                  type="submit"
                  disabled={!prompt.trim() || isSubmitting}
                  className="cta-button inline-flex items-center justify-center gap-2 rounded-full bg-[linear-gradient(135deg,#4f46e5,#7c3aed,#0891b2)] px-6 py-3 text-sm font-semibold text-white transition hover:scale-[1.005] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? t(lang, 'sending') : t(lang, 'startBuilding')}
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          </form>

          <div className="mx-auto mt-8 grid w-full max-w-5xl gap-4 lg:grid-cols-3">
            {inspirationCards.map((card, index) => (
              <button
                key={card.title}
                type="button"
                onClick={() => setPrompt(card.prompt)}
                className="inspiration-card rounded-[1.8rem] border border-white/10 bg-white/[0.05] p-5 text-left backdrop-blur-xl transition duration-300"
                style={{
                  animationDelay: `${index * 120}ms`,
                  backgroundImage:
                    'linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)), linear-gradient(135deg, rgba(79,70,229,0.12), rgba(8,145,178,0.06), rgba(124,58,237,0.12))',
                }}
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-[1.1rem] bg-white/8 text-indigo-200">
                  <card.icon size={20} />
                </div>
                <div className="mt-6 text-lg font-semibold text-white">{card.title}</div>
                <div className="mt-2 text-sm leading-6 text-white/52">{card.prompt}</div>
              </button>
            ))}
          </div>

          {recentProjects.length > 0 && (
            <section className="mx-auto mt-14 w-full max-w-6xl">
              <div className="mb-5 flex items-end justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-white">{t(lang, 'recentProjects')}</h2>
                  <p className="mt-1 text-sm text-white/48">{t(lang, 'recentProjectsSubtitle')}</p>
                </div>
              </div>

              <div className="flex gap-4 overflow-x-auto pb-3">
                {recentProjects.map((project) => (
                  <button
                    key={project.id}
                    type="button"
                    onClick={() => onSelectProject(project.id)}
                    className="recent-card min-w-[320px] max-w-[360px] flex-1 text-left"
                  >
                    <div className="recent-shell relative overflow-hidden rounded-[1.8rem] border border-white/10 bg-white/[0.06] backdrop-blur-2xl transition duration-300">
                      <div className="relative h-[160px] flex-shrink-0 overflow-hidden rounded-t-[1.8rem] bg-[#03050f]">
                        <iframe
                          title={`${project.name} preview`}
                          src={getPreviewUrl(project.id, 1)}
                          className="pointer-events-none absolute left-0 top-0 h-[640px] w-[400%] origin-top-left border-0 bg-white"
                          style={{ transform: 'scale(0.25)' }}
                        />
                      </div>
                      <div className="relative flex items-center gap-2.5 px-4 py-3 pl-5">
                        <span
                          className="h-2.5 w-2.5 flex-shrink-0 rounded-full"
                          style={{ backgroundColor: getStatusAccent(project.status) }}
                        />
                        <div className="min-w-0 flex-1 truncate text-sm font-semibold text-white">{project.name}</div>
                        <ArrowRight
                          size={18}
                          className="recent-arrow mt-0.5 shrink-0 -translate-x-3 opacity-0 text-indigo-200 transition duration-300"
                        />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </section>
          )}
        </section>
      </div>
    </div>
  );
};

export default ProjectsPage;
