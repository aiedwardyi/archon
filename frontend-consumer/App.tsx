import React, { useEffect, useState } from 'react';
import BackendConnectionOverlay from './components/BackendConnectionOverlay';
import SettingsModal from './components/SettingsModal';
import Sidebar from './components/Sidebar';
import { getLang, setLang } from './i18n';
import ProjectDetailPage from './pages/ProjectDetailPage';
import ProjectsPage from './pages/ProjectsPage';
import { backend, isNetworkError } from './services/orchestrator';
import { Project, SystemSettings } from './types';

function getInitialSettings(): SystemSettings {
  const saved = localStorage.getItem('adt_settings') || localStorage.getItem('da_settings');
  let parsed: any = null;

  if (saved) {
    try {
      parsed = JSON.parse(saved);
    } catch {
      parsed = null;
    }
  }
  const theme = parsed?.theme === 'dark' ? 'dark' : 'light';
  const language = parsed?.language === 'ko' || getLang() === 'ko' ? 'ko' : 'en';

  return {
    theme,
    language,
  };
}

const App: React.FC = () => {
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [hasNetworkError, setHasNetworkError] = useState(false);
  const [isOverlayDismissed, setIsOverlayDismissed] = useState(true);
  const [settings, setSettings] = useState<SystemSettings>(() => getInitialSettings());

  useEffect(() => {
    const update = () => {
      setProjects(backend.getProjects());
      setHasNetworkError(backend.getHasNetworkError());
      if (!backend.getHasNetworkError()) {
        setIsOverlayDismissed(true);
      }
    };

    update();
    return backend.subscribe(update);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    const body = document.body;

    root.classList.toggle('dark', settings.theme === 'dark');
    body.classList.toggle('dark', settings.theme === 'dark');
    root.classList.toggle('light', settings.theme === 'light');
    body.classList.toggle('light', settings.theme === 'light');
    setLang(settings.language);
    localStorage.setItem('adt_settings', JSON.stringify(settings));
  }, [settings]);

  const handleCreateProject = async (name: string, description: string) => {
    if (backend.getHasNetworkError()) {
      setIsOverlayDismissed(false);
      return;
    }

    try {
      const project = await backend.createProject(name, description);
      setCurrentProjectId(project.id);
      await backend.startExecution(project.id);
    } catch (error) {
      if (isNetworkError(error)) {
        setIsOverlayDismissed(false);
      }
      console.error('Failed to create project', error);
    }
  };

  const handleDeleteProject = async (id: string) => {
    try {
      await backend.deleteProject(id);
      if (currentProjectId === id) {
        setCurrentProjectId(null);
      }
    } catch (error) {
      console.error('Failed to delete project', error);
    }
  };

  const updateSettings = (updates: Partial<SystemSettings>) => {
    setSettings((current) => ({ ...current, ...updates }));
  };

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--app-bg)] text-[var(--app-fg)] transition-colors duration-300">
      {hasNetworkError && !isOverlayDismissed && (
        <BackendConnectionOverlay onClose={() => setIsOverlayDismissed(true)} />
      )}

      {currentProjectId && (
        <>
          {isSidebarOpen && (
            <button
              type="button"
              aria-label="Close sidebar"
              className="fixed inset-0 z-30 bg-slate-950/35 backdrop-blur-sm lg:hidden"
              onClick={() => setIsSidebarOpen(false)}
            />
          )}

          <Sidebar
            projects={projects}
            currentId={currentProjectId}
            onSelect={(id) => {
              setCurrentProjectId(id);
              setIsSidebarOpen(false);
            }}
            onNewProject={() => {
              setCurrentProjectId(null);
              setIsSidebarOpen(false);
            }}
            onOpenSettings={() => {
              setIsSettingsOpen(true);
              setIsSidebarOpen(false);
            }}
            onDeleteProject={handleDeleteProject}
            isOpen={isSidebarOpen}
            onClose={() => setIsSidebarOpen(false)}
          />
        </>
      )}

      <main className="relative flex-1 overflow-hidden">
        {currentProjectId ? (
          <ProjectDetailPage
            projectId={currentProjectId}
            onBack={() => setCurrentProjectId(null)}
            onOpenSidebar={() => setIsSidebarOpen(true)}
            onOpenSettings={() => setIsSettingsOpen(true)}
          />
        ) : (
          <ProjectsPage
            projects={projects}
            onCreateProject={handleCreateProject}
            onSelectProject={setCurrentProjectId}
            onOpenSettings={() => setIsSettingsOpen(true)}
          />
        )}
      </main>

      {isSettingsOpen && (
        <SettingsModal
          settings={settings}
          onUpdate={updateSettings}
          onClose={() => setIsSettingsOpen(false)}
        />
      )}
    </div>
  );
};

export default App;
