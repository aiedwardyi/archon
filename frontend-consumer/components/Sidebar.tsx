import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { MenuSquare, Plus, Settings, Trash2, X } from 'lucide-react';
import { backend } from '../services/orchestrator';
import { getLang, t } from '../i18n';
import { Project } from '../types';

interface SidebarProps {
  projects: Project[];
  currentId: string | null;
  onSelect: (id: string) => void;
  onNewProject: () => void;
  onOpenSettings: () => void;
  onDeleteProject: (id: string) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
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
  const lang = getLang();
  const [isConnected, setIsConnected] = useState(backend.getIsConnected());

  useEffect(() => {
    const update = () => setIsConnected(backend.getIsConnected());
    update();
    return backend.subscribe(update);
  }, []);

  const deletingProject = projects.find((project) => project.id === deletingProjectId);

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex w-[280px] flex-col border-r border-white/60 bg-white/95 px-5 pb-5 pt-6 shadow-[0_24px_60px_rgba(15,23,42,0.08)] backdrop-blur lg:relative lg:translate-x-0 dark:border-white/10 dark:bg-[#0f172a]/95 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } transition-transform duration-300`}
    >
      <div className="mb-6 flex items-center justify-between">
        <button
          type="button"
          onClick={onNewProject}
          className="flex items-center gap-3 text-left"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-white dark:bg-white dark:text-slate-950">
            <MenuSquare size={18} />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-950 dark:text-white">Archon</div>
            <div className="text-xs text-slate-500 dark:text-slate-300/70">{t(lang, 'heroHint')}</div>
          </div>
        </button>

        <button
          type="button"
          onClick={onClose}
          className="rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 lg:hidden dark:hover:bg-white/5 dark:hover:text-white"
          aria-label="Close sidebar"
        >
          <X size={18} />
        </button>
      </div>

      <div className="mb-5 flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs dark:border-white/10 dark:bg-white/5">
        <span className="font-medium text-slate-600 dark:text-slate-300">
          {isConnected ? t(lang, 'backendOnline') : t(lang, 'backendOffline')}
        </span>
        <span className={`h-2.5 w-2.5 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-amber-500'}`} />
      </div>

      <button
        type="button"
        onClick={onNewProject}
        className="mb-6 inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-100"
      >
        <Plus size={16} />
        {t(lang, 'startBuilding')}
      </button>

      <div className="flex-1 overflow-hidden">
        <div className="mb-3 text-xs font-medium uppercase tracking-[0.2em] text-slate-400 dark:text-slate-300/60">
          {t(lang, 'recentProjects')}
        </div>
        <div className="custom-scrollbar h-full space-y-2 overflow-y-auto pr-1">
          {projects.map((project) => (
            <button
              key={project.id}
              type="button"
              onClick={() => onSelect(project.id)}
              className={`group flex w-full items-start gap-3 rounded-2xl border px-4 py-3 text-left transition ${
                currentId === project.id
                  ? 'border-slate-950 bg-slate-950 text-white dark:border-white dark:bg-white dark:text-slate-950'
                  : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10'
              }`}
            >
              <div
                className={`mt-1 h-2.5 w-2.5 rounded-full ${
                  project.status === 'RUNNING'
                    ? 'bg-amber-500'
                    : project.status === 'COMPLETED'
                    ? 'bg-emerald-500'
                    : project.status === 'FAILED'
                    ? 'bg-rose-500'
                    : 'bg-slate-300 dark:bg-slate-600'
                }`}
              />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{project.name}</div>
                <div className="mt-1 line-clamp-2 text-xs opacity-70">{project.description}</div>
              </div>
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
                className={`rounded-full p-2 opacity-0 transition group-hover:opacity-100 ${
                  currentId === project.id
                    ? 'text-white/75 hover:bg-white/10 hover:text-white dark:text-slate-700 dark:hover:bg-slate-200'
                    : 'text-slate-400 hover:bg-slate-100 hover:text-rose-500 dark:hover:bg-white/10'
                }`}
                aria-label={t(lang, 'deleteProject')}
              >
                <Trash2 size={14} />
              </span>
            </button>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={onOpenSettings}
        className="mt-5 inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-100 dark:hover:bg-white/5"
      >
        <Settings size={16} />
        {t(lang, 'settings')}
      </button>

      {deletingProjectId &&
        createPortal(
          <div className="fixed inset-0 z-[120] flex items-center justify-center bg-slate-950/35 p-4 backdrop-blur-sm">
            <div className="w-full max-w-sm rounded-[2rem] border border-white/60 bg-white p-6 shadow-[0_30px_80px_rgba(15,23,42,0.16)] dark:border-white/10 dark:bg-[#111827]">
              <h3 className="text-lg font-semibold text-slate-950 dark:text-white">{t(lang, 'deleteConfirmTitle')}</h3>
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-300/70">{t(lang, 'deleteConfirmBody')}</p>
              <p className="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 dark:bg-white/5 dark:text-slate-100">
                {deletingProject?.name}
              </p>
              <div className="mt-5 flex gap-3">
                <button
                  type="button"
                  onClick={() => setDeletingProjectId(null)}
                  className="flex-1 rounded-2xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
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
                  className="flex-1 rounded-2xl bg-rose-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-rose-500"
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
