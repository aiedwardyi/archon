import React, { useState, useEffect } from 'react';
import { backend } from './services/orchestrator';
import { Project, SystemSettings } from './types';
import ProjectsPage from './pages/ProjectsPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import Sidebar from './components/Sidebar';
import SettingsModal from './components/SettingsModal';
import BackendConnectionOverlay from './components/BackendConnectionOverlay';
import { Menu } from 'lucide-react';

const App: React.FC = () => {
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isOverlayDismissed, setIsOverlayDismissed] = useState(true);

  const [settings, setSettings] = useState<SystemSettings>(() => {
    const saved = localStorage.getItem('adt_settings') || localStorage.getItem('da_settings');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return {
          model: parsed.model || 'Gemini 3 Pro',
          theme: parsed.theme || 'dark',
          username: parsed.username || 'AgentUser_01',
          email: parsed.email === 'user@devagents.app' ? 'user@ai-dev-team.app' : (parsed.email || 'user@ai-dev-team.app'),
          vibeLevel: parsed.vibeLevel !== undefined ? parsed.vibeLevel : 65,
          chatSuggestions: parsed.chatSuggestions !== undefined ? parsed.chatSuggestions : true,
          completionSound: parsed.completionSound || 'first'
        };
      } catch (e) {
        console.error("Failed to parse settings", e);
      }
    }
    return {
      model: 'Gemini 3 Pro',
      theme: 'dark',
      username: 'AgentUser_01',
      email: 'user@ai-dev-team.app',
      vibeLevel: 65,
      chatSuggestions: true,
      completionSound: 'first'
    };
  });

  useEffect(() => {
    const update = () => {
      const conn = backend.getIsConnected();
      setProjects(backend.getProjects());
      setIsConnected(conn);
      if (conn) setIsOverlayDismissed(true);
    };
    update();
    return backend.subscribe(update);
  }, []);

  useEffect(() => {
    if (settings.theme === 'light') {
      document.body.classList.add('light');
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    } else {
      document.body.classList.remove('light');
      document.documentElement.classList.remove('light');
      document.documentElement.classList.add('dark');
    }
    localStorage.setItem('adt_settings', JSON.stringify(settings));
  }, [settings]);

  const handleCreateProject = async (name: string, description: string) => {
    if (!backend.getIsConnected()) {
      setIsOverlayDismissed(false);
      return;
    }
    try {
      const project = await backend.createProject(name, description);
      setCurrentProjectId(project.id);
      backend.startExecution(project.id);
    } catch (error: any) {
      console.error("Failed to create project", error);
      setIsOverlayDismissed(false);
    }
  };

  const handleDeleteProject = async (id: string) => {
    await backend.deleteProject(id);
    if (currentProjectId === id) {
      setCurrentProjectId(null);
    }
  };

  const updateSettings = (updates: Partial<SystemSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  };

  return (
    <div className={`flex h-screen bg-background-light dark:bg-background text-slate-900 dark:text-slate-200 font-sans selection:bg-primary/30 overflow-hidden transition-colors duration-300`}>

      {!isConnected && !isOverlayDismissed && (
        <BackendConnectionOverlay onClose={() => setIsOverlayDismissed(true)} />
      )}

      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-[70] bg-black/50 backdrop-blur-sm lg:hidden animate-fade-in"
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
        theme={settings.theme}
        onToggleTheme={() => updateSettings({ theme: settings.theme === 'dark' ? 'light' : 'dark' })}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <main className="flex-1 relative overflow-hidden flex flex-col bg-background-light dark:bg-background">
        <div className="lg:hidden h-14 border-b border-slate-200 dark:border-white/5 flex items-center px-4 bg-white dark:bg-[#080a0f] z-30 shrink-0">
          <button
            onClick={() => setIsSidebarOpen(true)}
            className="p-2 -ml-2 text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-white transition-colors"
          >
            <Menu size={20} />
          </button>
          <span className="ml-2 font-bold text-sm text-slate-900 dark:text-white">ai-dev-team</span>
        </div>

        {currentProjectId ? (
          <ProjectDetailPage
            projectId={currentProjectId}
            onBack={() => setCurrentProjectId(null)}
          />
        ) : (
          <ProjectsPage
            onCreateProject={handleCreateProject}
            onSelectProject={setCurrentProjectId}
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
