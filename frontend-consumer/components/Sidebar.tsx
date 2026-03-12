import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { MenuSquare, Plus, Settings, Trash2, X } from 'lucide-react';
import { backend } from '../services/orchestrator';
import { getPreviewUrl } from '../services/orchestrator';
import { t, type Lang } from '../i18n';
import { Project } from '../types';

interface SidebarProps {
  lang: Lang;
  projects: Project[];
  currentId: string | null;
  onSelect: (id: string) => void;
  onNewProject: () => void;
  onOpenSettings: () => void;
  onDeleteProject: (id: string) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

function getStatusColor(status: Project['status']) {
  if (status === 'RUNNING') return '#f59e0b';
  if (status === 'COMPLETED') return '#10b981';
  if (status === 'FAILED') return '#fb7185';
  return '#64748b';
}

const Sidebar: React.FC<SidebarProps> = ({
  lang,
  projects,
  currentId,
  onSelect,
  onNewProject,
  onOpenSettings,
  onDeleteProject,
  isOpen = false,
  onClose,
}) => {
  const [deletingProjectId, setDeletingProjectId] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(backend.getIsConnected());

  useEffect(() => {
    const update = () => setIsConnected(backend.getIsConnected());
    update();
    return backend.subscribe(update);
  }, []);

  const deletingProject = projects.find((project) => project.id === deletingProjectId);

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex w-[280px] flex-col bg-[#050816] px-5 pb-5 pt-6 text-white shadow-[0_20px_80px_rgba(2,6,23,0.55)] transition-transform duration-300 lg:relative lg:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}
    >
      <style>{`
        @keyframes sidebarPulse {
          0% { transform: scale(1); opacity: 0.7; }
          70% { transform: scale(1.9); opacity: 0; }
          100% { transform: scale(1.9); opacity: 0; }
        }
        @keyframes sidebarShimmer {
          0% { background-position: 0% 50%; }
          100% { background-position: 200% 50%; }
        }
        @keyframes accentSlide {
          0% { transform: scaleY(0.25); opacity: 0; }
          100% { transform: scaleY(1); opacity: 1; }
        }
        .sidebar-start-text {
          background-image: linear-gradient(120deg, rgba(255,255,255,0.78), #ffffff, rgba(255,255,255,0.78));
          background-size: 200% auto;
          -webkit-background-clip: text;
          background-clip: text;
          color: transparent;
          animation: sidebarShimmer 2.4s linear infinite;
        }
        .sidebar-accent {
          animation: accentSlide 220ms ease-out;
          transform-origin: center;
        }
        button, a {
          -webkit-font-smoothing: antialiased;
          backface-visibility: hidden;
          transform: translateZ(0);
        }
      `}</style>

      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-48 bg-[radial-gradient(circle_at_top,rgba(79,70,229,0.32),transparent_70%)]" />
        <div className="absolute bottom-0 left-0 h-56 w-full bg-[radial-gradient(circle_at_bottom_left,rgba(8,145,178,0.18),transparent_70%)]" />
      </div>

      <div className="relative mb-6 flex items-center justify-between">
        <button type="button" onClick={onNewProject} className="flex items-center gap-3 text-left">
          <div className="flex h-11 w-11 items-center justify-center rounded-[1.4rem] border border-white/10 bg-white/5 text-indigo-200 backdrop-blur-xl">
            <MenuSquare size={18} />
          </div>
          <div>
            <div className="text-sm font-semibold tracking-[0.2em] text-white">Archon</div>
            <div className="text-xs uppercase tracking-[0.22em] text-white/38">Worlds in progress</div>
          </div>
        </button>

        <button
          type="button"
          onClick={onClose}
          className="rounded-full p-2 text-white/45 transition hover:bg-white/8 hover:text-white lg:hidden"
          aria-label="Close sidebar"
        >
          <X size={18} />
        </button>
      </div>

      <div className="relative mb-5 flex items-center justify-between rounded-[1.4rem] bg-white/[0.04] px-4 py-3 backdrop-blur-xl">
        <span className="text-xs font-medium uppercase tracking-[0.22em] text-white/55">
          {isConnected ? t(lang, 'backendOnline') : t(lang, 'backendOffline')}
        </span>
        <span className="relative inline-flex h-3 w-3 items-center justify-center">
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: isConnected ? '#10b981' : '#f59e0b' }}
          />
          {isConnected && (
            <span
              className="absolute inset-0 rounded-full border border-emerald-400/60"
              style={{ animation: 'sidebarPulse 1.8s ease-out infinite' }}
            />
          )}
        </span>
      </div>

      <button
        type="button"
        onClick={onNewProject}
        className="relative mb-6 inline-flex items-center justify-center gap-2 overflow-hidden rounded-[1.3rem] bg-[linear-gradient(135deg,#4f46e5,#7c3aed,#0891b2)] px-4 py-3 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(79,70,229,0.3)] transition hover:brightness-110"
      >
        <Plus size={16} />
        <span className="sidebar-start-text">{t(lang, 'startBuilding')}</span>
      </button>

      <div className="relative min-h-0 flex-1">
        <div className="mb-3 text-[11px] font-medium uppercase tracking-[0.3em] text-white/32">
          {t(lang, 'recentProjects')}
        </div>
        <div className="custom-scrollbar h-full space-y-2 overflow-y-auto pr-1">
          {projects.map((project) => {
            const isActive = currentId === project.id;
            return (
              <button
                key={project.id}
                type="button"
                onClick={() => onSelect(project.id)}
                className={`group relative flex w-full flex-col overflow-hidden rounded-[1.35rem] px-4 py-3 text-left transition ${
                  isActive
                    ? 'bg-white/[0.09] shadow-[0_14px_40px_rgba(79,70,229,0.2)]'
                    : 'bg-white/[0.03] hover:bg-white/[0.06]'
                }`}
              >
                {isActive && (
                  <span className="sidebar-accent absolute inset-y-3 left-0 w-1 rounded-r-full bg-indigo-500 shadow-[0_0_24px_rgba(99,102,241,0.8)]" />
                )}
                <div className="relative mb-3 h-[120px] w-full flex-shrink-0 overflow-hidden rounded-[1rem] bg-[#03050f]">
                  <iframe
                    title={`${project.name} thumbnail`}
                    src={getPreviewUrl(project.id, 1)}
                    className="pointer-events-none absolute left-0 top-0 h-[480px] w-[400%] origin-top-left border-0 bg-white"
                    style={{ transform: 'scale(0.25)', display: 'block' }}
                  />
                </div>
                <div className="flex w-full items-start gap-3">
                  <span
                    className="mt-1 h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: getStatusColor(project.status) }}
                  />
                  <span className="min-w-0 flex-1 pl-1">
                    <span className="block truncate text-sm font-medium text-white">{project.name}</span>
                  </span>
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(event) => {
                      event.stopPropagation();
                      setDeletingProjectId(project.id);
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        event.stopPropagation();
                        setDeletingProjectId(project.id);
                      }
                    }}
                    className="rounded-full p-2 text-white/26 opacity-0 transition group-hover:opacity-100 hover:bg-white/10 hover:text-rose-300"
                    aria-label={t(lang, 'deleteProject')}
                  >
                    <Trash2 size={14} />
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <button
        type="button"
        onClick={onOpenSettings}
        className="relative mt-5 inline-flex items-center justify-center gap-2 rounded-[1.3rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm font-medium text-white/72 backdrop-blur-xl transition hover:bg-white/[0.08] hover:text-white"
      >
        <Settings size={16} />
        {t(lang, 'settings')}
      </button>

      {deletingProjectId &&
        createPortal(
          <div className="fixed inset-0 z-[120] flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-md">
            <div className="w-full max-w-sm rounded-[2rem] border border-white/10 bg-[#09101f] p-6 text-white shadow-[0_30px_80px_rgba(2,6,23,0.55)]">
              <h3 className="text-lg font-semibold">{t(lang, 'deleteConfirmTitle')}</h3>
              <p className="mt-2 text-sm leading-6 text-white/58">{t(lang, 'deleteConfirmBody')}</p>
              <p className="mt-4 rounded-[1.2rem] bg-white/[0.05] px-4 py-3 text-sm font-medium text-white/82">
                {deletingProject?.name}
              </p>
              <div className="mt-5 flex gap-3">
                <button
                  type="button"
                  onClick={() => setDeletingProjectId(null)}
                  className="flex-1 rounded-[1.2rem] border border-white/10 px-4 py-3 text-sm font-medium text-white/68 transition hover:bg-white/[0.05] hover:text-white"
                >
                  {t(lang, 'cancel')}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (deletingProjectId) {
                      onDeleteProject(deletingProjectId);
                    }
                    setDeletingProjectId(null);
                  }}
                  className="flex-1 rounded-[1.2rem] bg-rose-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-rose-500"
                >
                  {t(lang, 'confirmDelete')}
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </aside>
  );
};

export default Sidebar;
