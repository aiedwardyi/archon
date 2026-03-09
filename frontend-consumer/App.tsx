import React, { useEffect, useState } from 'react';
import BackendConnectionOverlay from './components/BackendConnectionOverlay';
import SettingsModal from './components/SettingsModal';
import Sidebar from './components/Sidebar';
import { getLang, setLang } from './i18n';
import LoginPage from './pages/LoginPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import ProjectsPage from './pages/ProjectsPage';
import RegisterPage from './pages/RegisterPage';
import { AuthUser, clearStoredSession, fetchCurrentUser, getStoredToken, getStoredUser, logout } from './services/auth';
import { backend, isAuthError, isNetworkError } from './services/orchestrator';
import { Project, SystemSettings } from './types';

const THEME_PREFERENCE_KEY = 'archon_consumer_theme_preference';

interface AppLocation {
  pathname: string;
  search: string;
}

function readLocation(): AppLocation {
  return {
    pathname: window.location.pathname,
    search: window.location.search,
  };
}

function getInitialSettings(): SystemSettings {
  const saved = localStorage.getItem('adt_settings') || localStorage.getItem('da_settings');
  let parsed: unknown = null;

  if (saved) {
    try {
      parsed = JSON.parse(saved);
    } catch {
      parsed = null;
    }
  }

  const explicitTheme = localStorage.getItem(THEME_PREFERENCE_KEY);
  const theme = explicitTheme === 'dark' || explicitTheme === 'light' ? explicitTheme : 'light';
  const language = (parsed as { language?: string } | null)?.language === 'ko' || getLang() === 'ko' ? 'ko' : 'en';

  return {
    theme,
    language,
  };
}

function normalizePath(pathname: string) {
  const normalized = pathname.replace(/\/+$/, '') || '/';
  if (normalized === '/login') return '/login';
  if (normalized === '/register') return '/register';
  if (normalized === '/projects') return '/projects';
  return '/';
}

const App: React.FC = () => {
  const [location, setLocation] = useState<AppLocation>(() => readLocation());
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [hasNetworkError, setHasNetworkError] = useState(false);
  const [isOverlayDismissed, setIsOverlayDismissed] = useState(true);
  const [hasSession, setHasSession] = useState<boolean>(() => Boolean(getStoredToken()));
  const [authUser, setAuthUser] = useState<AuthUser | null>(() => getStoredUser());
  const [settings, setSettings] = useState<SystemSettings>(() => getInitialSettings());

  const navigate = (href: string, options?: { replace?: boolean }) => {
    const next = new URL(href, window.location.origin);
    const method = options?.replace ? 'replaceState' : 'pushState';
    window.history[method]({}, '', `${next.pathname}${next.search}${next.hash}`);
    setLocation(readLocation());
  };

  const handleAuthError = () => {
    clearStoredSession();
    backend.clearProjects();
    setAuthUser(null);
    setHasSession(false);
    setCurrentProjectId(null);
  };

  const handleAuthSuccess = (user: AuthUser) => {
    setAuthUser(user);
    setHasSession(true);
  };

  const handleSignOut = async () => {
    await logout();
    backend.clearProjects();
    setAuthUser(null);
    setHasSession(false);
    setCurrentProjectId(null);
    setIsSidebarOpen(false);
    navigate('/', { replace: true });
  };

  useEffect(() => {
    const syncLocation = () => setLocation(readLocation());
    const syncSession = () => {
      setHasSession(Boolean(getStoredToken()));
      setAuthUser(getStoredUser());
    };

    window.addEventListener('popstate', syncLocation);
    window.addEventListener('storage', syncSession);

    return () => {
      window.removeEventListener('popstate', syncLocation);
      window.removeEventListener('storage', syncSession);
    };
  }, []);

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
    localStorage.setItem(
      'adt_settings',
      JSON.stringify({
        ...settings,
        themePreferenceSet: Boolean(localStorage.getItem(THEME_PREFERENCE_KEY)),
      })
    );
  }, [settings]);

  useEffect(() => {
    if (!hasSession) return;

    const loadProjects = async () => {
      try {
        await backend.fetchProjects();
        if (backend.getProjects().length === 0) {
          await backend.seedProjects();
          await backend.fetchProjects();
        }
      } catch (error) {
        if (isAuthError(error)) {
          handleAuthError();
        }
      }
    };

    if (!authUser) {
      void fetchCurrentUser()
        .then((user) => {
          setAuthUser(user);
        })
        .catch(() => {
          handleAuthError();
        });
    }

    void loadProjects();
  }, [authUser, hasSession]);

  useEffect(() => {
    const path = normalizePath(location.pathname);
    if (hasSession && (path === '/login' || path === '/register')) {
      navigate('/projects', { replace: true });
    }
  }, [hasSession, location.pathname]);

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
      if (isAuthError(error)) {
        handleAuthError();
      }
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
    if (updates.theme) {
      localStorage.setItem(THEME_PREFERENCE_KEY, updates.theme);
    }
    setSettings((current) => ({ ...current, ...updates }));
  };

  const path = normalizePath(location.pathname);

  if (path === '/login') {
    return <LoginPage onAuthSuccess={handleAuthSuccess} onNavigate={navigate} />;
  }

  if (path === '/register') {
    return <RegisterPage onAuthSuccess={handleAuthSuccess} onNavigate={navigate} />;
  }

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
            hasSession={hasSession}
            authUser={authUser}
            onAuthError={handleAuthError}
            onBack={() => setCurrentProjectId(null)}
            onOpenSidebar={() => setIsSidebarOpen(true)}
            onOpenSettings={() => setIsSettingsOpen(true)}
            onNavigate={navigate}
            onSignOut={handleSignOut}
          />
        ) : (
          <ProjectsPage
            projects={projects}
            hasSession={hasSession}
            authUser={authUser}
            onCreateProject={handleCreateProject}
            onSelectProject={setCurrentProjectId}
            onOpenSettings={() => setIsSettingsOpen(true)}
            onNavigate={navigate}
            onSignOut={handleSignOut}
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
