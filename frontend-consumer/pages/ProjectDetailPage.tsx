import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowLeft,
  Clock3,
  Code2,
  FileCode2,
  FileText,
  History,
  Layers3,
  Loader2,
  Menu,
  Monitor,
  RefreshCw,
  RotateCcw,
  Settings2,
  Smartphone,
  Sparkles,
} from 'lucide-react';
import ArtifactViewer from '../components/ArtifactViewer';
import { getLang, t } from '../i18n';
import {
  backend,
  classifyProjectMessage,
  fetchBrief,
  fetchChatHistory,
  fetchCodeArtifact,
  fetchPlan,
  fetchProjectHead,
  fetchVersionFile,
  fetchVersionTree,
  fetchVersions,
  getPreviewUrl,
  isNetworkError,
  PromptHistoryEntry,
  restoreVersion,
  saveChatMessages,
  VersionRecord,
  VersionTreeNode,
} from '../services/orchestrator';
import { Artifact, EngineerTask, Project } from '../types';

interface ProjectDetailPageProps {
  projectId: string;
  onBack: () => void;
  onOpenSidebar: () => void;
  onOpenSettings: () => void;
}

type ActiveTab = 'preview' | 'brief' | 'buildPlan' | 'code' | 'changes' | 'versions';
type RemoteState<T> = { loading: boolean; error: boolean; data: T | null };
type CodeFileRecord = { filename: string; content: string; language: string };

const EMPTY_REMOTE = { loading: false, error: false, data: null };

function flattenTree(nodes: VersionTreeNode[]): string[] {
  const files: string[] = [];
  nodes.forEach((node) => {
    if (node.type === 'file') files.push(node.path);
    if (node.children) files.push(...flattenTree(node.children));
  });
  return files;
}

function formatTimestamp(value?: string | number) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function getStatusLabel(project: Project, lang: ReturnType<typeof getLang>) {
  if (project.status === 'COMPLETED') return t(lang, 'statusCompleted');
  if (project.status === 'FAILED') return t(lang, 'statusFailed');
  if (project.status === 'RUNNING') return t(lang, 'statusRunning');
  return t(lang, 'statusIdle');
}

function getProgress(project?: Project) {
  if (!project) return 0;
  if (project.status === 'COMPLETED') return 100;
  if (project.status !== 'RUNNING') return 0;
  if (project.currentStage === 'pm') return 28;
  if (project.currentStage === 'planner') return 58;
  if (project.currentStage === 'engineer') return 86;
  return 12;
}

const EmptyPanel: React.FC<{ icon: React.ReactNode; title: string; detail?: string }> = ({ icon, title, detail }) => (
  <div className="flex min-h-[360px] flex-col items-center justify-center rounded-[2rem] border border-slate-200 bg-white px-6 text-center shadow-sm dark:border-white/10 dark:bg-[#111827]">
    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600 dark:bg-white/5 dark:text-slate-200">{icon}</div>
    <h3 className="mt-5 text-lg font-semibold text-slate-950 dark:text-white">{title}</h3>
    {detail && <p className="mt-2 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-300/70">{detail}</p>}
  </div>
);

const Bubble: React.FC<{ message: PromptHistoryEntry }> = ({ message }) => {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[88%] rounded-[1.5rem] px-4 py-3 text-sm leading-6 shadow-sm ${
          isUser
            ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
            : 'border border-slate-200 bg-white text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-100'
        }`}
      >
        <div>{message.content}</div>
        {message.timestamp && <div className="mt-2 text-xs opacity-70">{formatTimestamp(message.timestamp)}</div>}
      </div>
    </div>
  );
};

const CodePanel: React.FC<{ lang: ReturnType<typeof getLang>; projectId: string; version: number | null }> = ({ lang, projectId, version }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [files, setFiles] = useState<CodeFileRecord[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!version) {
        setFiles([]);
        setSelected(null);
        setError(false);
        return;
      }
      setLoading(true);
      setError(false);
      try {
        const tree = await fetchVersionTree(projectId, version);
        const paths = flattenTree(tree.tree || []);
        const loaded = await Promise.all(
          paths.map(async (path) => {
            const file = await fetchVersionFile(projectId, version, path);
            return { filename: path, content: file.content || '', language: file.language || 'text' };
          })
        );
        if (!cancelled) {
          setFiles(loaded);
          setSelected(loaded[0]?.filename || null);
        }
      } catch {
        if (!cancelled) {
          setFiles([]);
          setSelected(null);
          setError(true);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId, version]);

  const activeFile = files.find((file) => file.filename === selected);
  if (!version) return <EmptyPanel icon={<Code2 size={22} />} title={t(lang, 'noCodeYet')} />;
  if (loading) return <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'sending')} />;
  if (error) return <EmptyPanel icon={<RefreshCw size={22} />} title={t(lang, 'couldNotLoad')} />;
  if (files.length === 0) return <EmptyPanel icon={<Code2 size={22} />} title={t(lang, 'noCodeYet')} />;
  return (
    <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#111827]">
      <div className="grid min-h-[520px] lg:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="border-b border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30 lg:border-b-0 lg:border-r">
          <div className="mb-4 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.2em] text-slate-400 dark:text-slate-300/60">
            <FileCode2 size={14} />
            {t(lang, 'files')}
          </div>
          <div className="space-y-2">
            {files.map((file) => (
              <button
                key={file.filename}
                type="button"
                onClick={() => setSelected(file.filename)}
                className={`block w-full rounded-2xl px-3 py-2 text-left text-sm transition ${
                  selected === file.filename
                    ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
                    : 'text-slate-600 hover:bg-white hover:text-slate-950 dark:text-slate-200 dark:hover:bg-white/10 dark:hover:text-white'
                }`}
              >
                <div className="truncate font-medium">{file.filename}</div>
              </button>
            ))}
          </div>
        </aside>
        <div className="min-w-0">
          {activeFile ? (
            <>
              <div className="border-b border-slate-200 px-5 py-4 text-xs text-slate-400 dark:border-white/10 dark:text-slate-300/60">{activeFile.language}</div>
              <pre className="custom-scrollbar overflow-auto p-5 text-sm leading-6 text-slate-800 dark:text-slate-100">{activeFile.content}</pre>
            </>
          ) : (
            <EmptyPanel icon={<Code2 size={22} />} title={t(lang, 'selectFile')} />
          )}
        </div>
      </div>
    </div>
  );
};

const ProjectDetailPage: React.FC<ProjectDetailPageProps> = ({ projectId, onBack, onOpenSidebar, onOpenSettings }) => {
  const lang = getLang();
  const [project, setProject] = useState<Project | undefined>(undefined);
  const [activeTab, setActiveTab] = useState<ActiveTab>('preview');
  const [version, setVersion] = useState<number | null>(null);
  const [viewport, setViewport] = useState<'desktop' | 'mobile'>('desktop');
  const [messages, setMessages] = useState<PromptHistoryEntry[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [versionsState, setVersionsState] = useState({
    loading: true,
    error: false,
    restoringId: null as string | null,
    selectedId: null as string | null,
    versions: [] as VersionRecord[],
  });
  const [briefState, setBriefState] = useState<RemoteState<any>>(EMPTY_REMOTE);
  const [planState, setPlanState] = useState<RemoteState<Artifact>>(EMPTY_REMOTE);
  const [changesState, setChangesState] = useState<RemoteState<EngineerTask[]>>(EMPTY_REMOTE);
  const [headError, setHeadError] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sync = () => setProject(backend.getProject(projectId));
    sync();
    return backend.subscribe(sync);
  }, [projectId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, project?.status]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const history = await fetchChatHistory(projectId);
        if (!cancelled) setMessages(history || []);
      } catch {
        if (!cancelled) setMessages([]);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const head = await fetchProjectHead(projectId);
        if (!cancelled) {
          setVersion(Number(head.version));
          setHeadError(false);
        }
      } catch {
        if (!cancelled) {
          setVersion(null);
          setHeadError(true);
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId, project?.status]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setVersionsState((current) => ({ ...current, loading: true, error: false }));
      try {
        const versions = await fetchVersions(projectId);
        if (!cancelled) {
          setVersionsState((current) => ({
            ...current,
            loading: false,
            error: false,
            versions,
            selectedId: current.selectedId && versions.some((item) => item.id === current.selectedId) ? current.selectedId : versions[0]?.id || null,
          }));
        }
      } catch {
        if (!cancelled) {
          setVersionsState({ loading: false, error: true, restoringId: null, selectedId: null, versions: [] });
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId, project?.status]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!version) {
        setBriefState({ loading: false, error: headError, data: null });
        setPlanState({ loading: false, error: headError, data: null });
        setChangesState({ loading: false, error: headError, data: null });
        return;
      }

      setBriefState({ loading: true, error: false, data: null });
      setPlanState({ loading: true, error: false, data: null });
      setChangesState({ loading: true, error: false, data: null });

      const [brief, plan, code] = await Promise.allSettled([
        fetchBrief(projectId, version),
        fetchPlan(projectId, version),
        fetchCodeArtifact(projectId, version),
      ]);
      if (cancelled) return;

      setBriefState(brief.status === 'fulfilled' ? { loading: false, error: false, data: brief.value } : { loading: false, error: true, data: null });
      setPlanState(
        plan.status === 'fulfilled'
          ? {
              loading: false,
              error: false,
              data: {
                id: `plan-${projectId}-${version}`,
                projectId,
                type: 'PLAN',
                title: t(lang, 'buildPlan'),
                content: plan.value,
                createdAt: Date.now(),
                agent: 'Archon',
              },
            }
          : { loading: false, error: true, data: null }
      );
      setChangesState(code.status === 'fulfilled' ? { loading: false, error: false, data: code.value.tasks } : { loading: false, error: true, data: null });
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId, version, lang, headError]);

  const selectedVersion = useMemo(
    () => versionsState.versions.find((item) => item.id === versionsState.selectedId) || null,
    [versionsState.selectedId, versionsState.versions]
  );
  const progress = getProgress(project);
  const statusMessage =
    project?.status === 'FAILED'
      ? t(lang, 'buildFailed')
      : project?.status === 'COMPLETED'
      ? t(lang, 'buildReady')
      : project?.currentStage === 'pm'
      ? t(lang, 'creatingBrief')
      : project?.currentStage === 'planner'
      ? t(lang, 'planningBuild')
      : project?.currentStage === 'engineer'
      ? t(lang, 'writingCode')
      : t(lang, 'buildingApp');
  const tabs = [
    { id: 'preview' as const, label: t(lang, 'preview'), icon: Monitor },
    { id: 'brief' as const, label: t(lang, 'brief'), icon: FileText },
    { id: 'buildPlan' as const, label: t(lang, 'buildPlan'), icon: Layers3 },
    { id: 'code' as const, label: t(lang, 'code'), icon: Code2 },
    { id: 'changes' as const, label: t(lang, 'changes'), icon: History },
    { id: 'versions' as const, label: t(lang, 'versions'), icon: Clock3 },
  ];

  const handleSendMessage = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!chatInput.trim() || chatLoading || project?.status === 'RUNNING') return;

    const userMessage: PromptHistoryEntry = {
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date().toISOString(),
    };
    const nextMessages = [...messages, userMessage];

    setMessages(nextMessages);
    setChatInput('');
    setChatLoading(true);

    try {
      const response = await classifyProjectMessage(projectId, userMessage.content);
      if (response.response_type === 'chat') {
        const assistantMessage: PromptHistoryEntry = {
          role: 'assistant',
          content: response.message || '',
          timestamp: new Date().toISOString(),
        };
        const updated = [...nextMessages, assistantMessage];
        setMessages(updated);
        await saveChatMessages(projectId, updated);
      } else {
        setActiveTab('preview');
        await backend.startIteration(projectId, userMessage.content, nextMessages);
      }
    } catch (error) {
      if (isNetworkError(error)) {
        setMessages((current) => current.slice(0, -1));
      }
      console.error('Failed to handle project chat', error);
    } finally {
      setChatLoading(false);
    }
  };

  const handleRestore = async () => {
    if (!selectedVersion || versionsState.restoringId) return;
    setVersionsState((current) => ({ ...current, restoringId: selectedVersion.id }));
    try {
      await restoreVersion(selectedVersion.id);
      await backend.fetchProjects().catch(() => undefined);
      const head = await fetchProjectHead(projectId);
      const versions = await fetchVersions(projectId);
      setVersion(Number(head.version));
      setVersionsState((current) => ({ ...current, restoringId: null, versions, selectedId: selectedVersion.id }));
      setActiveTab('preview');
    } catch (error) {
      console.error('Failed to restore version', error);
      setVersionsState((current) => ({ ...current, restoringId: null }));
    }
  };

  if (!project) {
    return (
      <div className="flex h-full items-center justify-center bg-[var(--app-bg)] text-sm text-slate-500 dark:text-slate-300">
        <Loader2 size={18} className="mr-2 animate-spin" />
        {t(lang, 'sending')}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-[var(--app-bg)]">
      <header className="border-b border-slate-200/80 bg-white/80 px-4 py-3 backdrop-blur dark:border-white/10 dark:bg-[#0f172a]/80 sm:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              onClick={onOpenSidebar}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 lg:hidden dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10"
              aria-label="Open sidebar"
            >
              <Menu size={18} />
            </button>
            <button
              type="button"
              onClick={onBack}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10"
              aria-label="Back to home"
            >
              <ArrowLeft size={18} />
            </button>
            <div className="min-w-0">
              <div className="text-sm font-semibold text-slate-950 dark:text-white">{project.name}</div>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-300/70">
                <span className="line-clamp-1">{project.description}</span>
                <span className="hidden h-1 w-1 rounded-full bg-slate-300 sm:inline-block dark:bg-slate-500" />
                <span>{t(lang, 'savedVersionsHint')}</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`rounded-full px-3 py-1.5 text-xs font-medium ${
                project.status === 'COMPLETED'
                  ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300'
                  : project.status === 'FAILED'
                  ? 'bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300'
                  : project.status === 'RUNNING'
                  ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300'
                  : 'bg-slate-100 text-slate-700 dark:bg-white/5 dark:text-slate-200'
              }`}
            >
              {getStatusLabel(project, lang)}
            </span>
            <button
              type="button"
              onClick={onOpenSettings}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10"
              aria-label="Open settings"
            >
              <Settings2 size={18} />
            </button>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition ${
                activeTab === tab.id
                  ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
                  : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10'
              }`}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      <div className="grid min-h-0 flex-1 gap-6 overflow-hidden p-4 sm:p-6 lg:grid-cols-[340px_minmax(0,1fr)]">
        <aside className="custom-scrollbar order-2 overflow-y-auto lg:order-1">
          <div className="rounded-[2rem] border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#111827]">
            <div className="border-b border-slate-200 px-5 py-4 dark:border-white/10">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-950 dark:text-white">
                <Sparkles size={16} />
                {t(lang, 'projectConversation')}
              </div>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-300/70">{t(lang, 'savedVersionsHint')}</p>
            </div>
            <div className="custom-scrollbar max-h-[420px] space-y-4 overflow-y-auto px-5 py-5 lg:h-[calc(100vh-27rem)] lg:max-h-none">
              <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5">
                <div className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400 dark:text-slate-300/60">{t(lang, 'originalPrompt')}</div>
                <div className="mt-3 text-sm leading-6 text-slate-700 dark:text-slate-100">{project.description}</div>
              </div>
              {messages.length > 0 ? (
                messages.map((message, index) => <Bubble key={`${message.role}-${index}-${message.content}`} message={message} />)
              ) : (
                <div className="rounded-[1.5rem] border border-dashed border-slate-300 p-4 text-sm text-slate-500 dark:border-white/10 dark:text-slate-300/70">
                  {t(lang, 'emptyConversation')}
                </div>
              )}
              {project.status === 'RUNNING' && (
                <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-4 dark:border-amber-500/20 dark:bg-amber-500/10">
                  <div className="flex items-center gap-3">
                    <Loader2 size={18} className="animate-spin text-amber-600 dark:text-amber-300" />
                    <div>
                      <div className="text-sm font-medium text-amber-900 dark:text-amber-100">{statusMessage}</div>
                      <div className="mt-1 text-xs text-amber-700 dark:text-amber-200/80">{progress}%</div>
                    </div>
                  </div>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-amber-100 dark:bg-white/10">
                    <div className="h-full rounded-full bg-amber-500 transition-all duration-500" style={{ width: `${progress}%` }} />
                  </div>
                </div>
              )}
              {project.status === 'COMPLETED' && <div className="rounded-[1.5rem] border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-100">{t(lang, 'buildReady')}</div>}
              {project.status === 'FAILED' && <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-100">{t(lang, 'buildFailed')}</div>}
              <div ref={endRef} />
            </div>
            <form onSubmit={handleSendMessage} className="border-t border-slate-200 px-5 py-4 dark:border-white/10">
              <textarea
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                disabled={chatLoading || project.status === 'RUNNING'}
                placeholder={project.status === 'RUNNING' ? t(lang, 'buildInProgress') : t(lang, 'chatComposerPlaceholder')}
                className="min-h-[120px] w-full resize-none rounded-[1.5rem] border border-slate-200 bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-300 focus:bg-white dark:border-white/10 dark:bg-slate-950/40 dark:text-white dark:placeholder:text-slate-400/70 dark:focus:bg-slate-950"
              />
              <button
                type="submit"
                disabled={!chatInput.trim() || chatLoading || project.status === 'RUNNING'}
                className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-100"
              >
                {chatLoading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
                {chatLoading ? t(lang, 'thinking') : t(lang, 'askForChanges')}
              </button>
            </form>
          </div>
        </aside>

        <section className="custom-scrollbar order-1 overflow-y-auto lg:order-2">
          {activeTab === 'preview' &&
            (version ? (
              <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#111827]">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-white/10">
                  <div>
                    <div className="text-sm font-semibold text-slate-950 dark:text-white">{t(lang, 'latestVersion')}</div>
                    <div className="mt-1 text-sm text-slate-500 dark:text-slate-300/70">
                      {t(lang, 'versionHistory')} {version}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setViewport('desktop')}
                      className={`rounded-full p-2 transition ${
                        viewport === 'desktop'
                          ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
                          : 'border border-slate-200 bg-white text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-200'
                      }`}
                      aria-label="Desktop preview"
                    >
                      <Monitor size={16} />
                    </button>
                    <button
                      type="button"
                      onClick={() => setViewport('mobile')}
                      className={`rounded-full p-2 transition ${
                        viewport === 'mobile'
                          ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
                          : 'border border-slate-200 bg-white text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-200'
                      }`}
                      aria-label="Mobile preview"
                    >
                      <Smartphone size={16} />
                    </button>
                  </div>
                </div>
                <div className="bg-slate-100 p-4 dark:bg-slate-950/40 sm:p-6">
                  {viewport === 'desktop' ? (
                    <iframe title="Project preview" src={getPreviewUrl(projectId, version)} className="h-[70vh] w-full rounded-[1.5rem] border-0 bg-white shadow-sm" />
                  ) : (
                    <div className="mx-auto w-[375px] max-w-full overflow-hidden rounded-[2.25rem] border-[10px] border-slate-950 bg-white shadow-2xl dark:border-slate-200">
                      <iframe title="Project preview mobile" src={getPreviewUrl(projectId, version)} className="h-[70vh] w-full border-0 bg-white" />
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <EmptyPanel icon={<Monitor size={22} />} title={headError ? t(lang, 'couldNotLoad') : t(lang, 'noPreviewYet')} detail={headError ? undefined : t(lang, 'savedVersionsHint')} />
            ))}

          {activeTab === 'brief' &&
            (briefState.loading ? (
              <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'sending')} />
            ) : briefState.error ? (
              <EmptyPanel icon={<RefreshCw size={22} />} title={t(lang, 'couldNotLoad')} />
            ) : briefState.data ? (
              <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-[#111827] sm:p-8">
                <h2 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">{briefState.data.title}</h2>
                <p className="mt-4 text-base leading-7 text-slate-600 dark:text-slate-200/80">{briefState.data.summary}</p>
                <div className="mt-8 grid gap-6 lg:grid-cols-2">
                  <section className="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-white/5">
                    <h3 className="text-sm font-semibold text-slate-950 dark:text-white">{t(lang, 'brief')}</h3>
                    <ul className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-200/80">
                      {(briefState.data.features || []).map((feature: string) => (
                        <li key={feature} className="rounded-2xl bg-white px-4 py-3 dark:bg-slate-950/40">
                          {feature}
                        </li>
                      ))}
                    </ul>
                  </section>
                  <section className="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-white/5">
                    <h3 className="text-sm font-semibold text-slate-950 dark:text-white">{t(lang, 'buildPlan')}</h3>
                    <ul className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-200/80">
                      {(briefState.data.techStackRecommendation || []).map((item: string) => (
                        <li key={item} className="rounded-2xl bg-white px-4 py-3 dark:bg-slate-950/40">
                          {item}
                        </li>
                      ))}
                    </ul>
                  </section>
                </div>
              </div>
            ) : (
              <EmptyPanel icon={<FileText size={22} />} title={t(lang, 'noBriefYet')} />
            ))}

          {activeTab === 'buildPlan' &&
            (planState.loading ? (
              <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'sending')} />
            ) : planState.error ? (
              <EmptyPanel icon={<RefreshCw size={22} />} title={t(lang, 'couldNotLoad')} />
            ) : planState.data ? (
              <ArtifactViewer artifact={planState.data} />
            ) : (
              <EmptyPanel icon={<Layers3 size={22} />} title={t(lang, 'noPlanYet')} />
            ))}

          {activeTab === 'code' && <CodePanel lang={lang} projectId={projectId} version={version} />}

          {activeTab === 'changes' &&
            (changesState.loading ? (
              <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'sending')} />
            ) : changesState.error ? (
              <EmptyPanel icon={<RefreshCw size={22} />} title={t(lang, 'couldNotLoad')} />
            ) : changesState.data && changesState.data.length > 0 ? (
              <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm dark:border-white/10 dark:bg-[#111827] sm:p-8">
                <h2 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">{t(lang, 'whatChangedTitle')}</h2>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-300/70">{t(lang, 'whatChangedSubtitle')}</p>
                <div className="mt-8 space-y-4">
                  {changesState.data.map((task) => (
                    <div key={task.id} className="rounded-[1.5rem] border border-slate-200 bg-slate-50 px-5 py-4 dark:border-white/10 dark:bg-white/5">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div className="text-sm font-semibold text-slate-950 dark:text-white">{task.filename}</div>
                        <div className="text-xs text-slate-400 dark:text-slate-300/60">{formatTimestamp(task.timestamp)}</div>
                      </div>
                      <div className="mt-2 text-sm text-slate-600 dark:text-slate-200/80">{task.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyPanel icon={<History size={22} />} title={t(lang, 'couldNotLoad')} />
            ))}

          {activeTab === 'versions' &&
            (versionsState.loading ? (
              <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'loadingVersions')} />
            ) : versionsState.error ? (
              <EmptyPanel icon={<RefreshCw size={22} />} title={t(lang, 'couldNotLoad')} />
            ) : versionsState.versions.length === 0 ? (
              <EmptyPanel icon={<Clock3 size={22} />} title={t(lang, 'noVersionsYet')} />
            ) : (
              <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#111827]">
                <div className="grid min-h-[560px] lg:grid-cols-[320px_minmax(0,1fr)]">
                  <aside className="border-b border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30 lg:border-b-0 lg:border-r">
                    <div className="mb-4">
                      <div className="text-sm font-semibold text-slate-950 dark:text-white">{t(lang, 'versionHistory')}</div>
                      <div className="mt-1 text-sm text-slate-500 dark:text-slate-300/70">{t(lang, 'savedVersionsHint')}</div>
                    </div>
                    <div className="space-y-2">
                      {versionsState.versions.map((item) => {
                        const promptPreview =
                          item.prompt_history?.filter((entry) => entry.role === 'user').slice(-1)[0]?.content ||
                          t(lang, 'promptVersionFallback');
                        return (
                          <button
                            key={item.id}
                            type="button"
                            onClick={() => setVersionsState((current) => ({ ...current, selectedId: item.id }))}
                            className={`block w-full rounded-[1.5rem] border px-4 py-3 text-left transition ${
                              versionsState.selectedId === item.id
                                ? 'border-slate-950 bg-slate-950 text-white dark:border-white dark:bg-white dark:text-slate-950'
                                : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 dark:border-white/10 dark:bg-white/5 dark:text-slate-100 dark:hover:bg-white/10'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-3">
                              <div className="text-sm font-semibold">v{item.version}</div>
                              <div className="text-xs opacity-70">{formatTimestamp(item.created_at)}</div>
                            </div>
                            <div className="mt-2 line-clamp-2 text-sm opacity-80">{promptPreview}</div>
                          </button>
                        );
                      })}
                    </div>
                  </aside>
                  <div className="min-w-0 p-4 sm:p-6">
                    {selectedVersion ? (
                      <div className="flex h-full flex-col gap-5">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <div className="text-lg font-semibold text-slate-950 dark:text-white">v{selectedVersion.version}</div>
                            <div className="mt-1 text-sm text-slate-500 dark:text-slate-300/70">{formatTimestamp(selectedVersion.created_at)}</div>
                          </div>
                          <button
                            type="button"
                            onClick={handleRestore}
                            disabled={versionsState.restoringId === selectedVersion.id}
                            className="inline-flex items-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-100"
                          >
                            {versionsState.restoringId === selectedVersion.id ? <Loader2 size={16} className="animate-spin" /> : <RotateCcw size={16} />}
                            {versionsState.restoringId === selectedVersion.id ? t(lang, 'restoring') : t(lang, 'restoreVersion')}
                          </button>
                        </div>
                        <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5">
                          <div className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400 dark:text-slate-300/60">{t(lang, 'askForChanges')}</div>
                          <div className="mt-3 text-sm leading-6 text-slate-700 dark:text-slate-100">
                            {selectedVersion.prompt_history?.filter((entry) => entry.role === 'user').slice(-1)[0]?.content || t(lang, 'promptVersionFallback')}
                          </div>
                        </div>
                        <div className="flex-1 rounded-[1.5rem] border border-slate-200 bg-slate-100 p-4 dark:border-white/10 dark:bg-slate-950/40">
                          <iframe
                            title={`Version ${selectedVersion.version} preview`}
                            src={getPreviewUrl(projectId, selectedVersion.version)}
                            className="h-[55vh] w-full rounded-[1.25rem] border-0 bg-white"
                          />
                        </div>
                      </div>
                    ) : (
                      <EmptyPanel icon={<Clock3 size={22} />} title={t(lang, 'selectVersion')} />
                    )}
                  </div>
                </div>
              </div>
            ))}
        </section>
      </div>
    </div>
  );
};

export default ProjectDetailPage;
