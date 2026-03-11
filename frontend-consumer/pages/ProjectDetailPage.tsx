import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlignLeft,
  ArrowLeft,
  ArrowRight,
  ChevronDown,
  Clock3,
  Code2,
  ExternalLink,
  FileCode2,
  FileText,
  Globe2,
  History,
  Layers3,
  Lightbulb,
  Loader2,
  Menu,
  Monitor,
  Palette,
  RefreshCw,
  RotateCcw,
  Settings2,
  Smartphone,
  Sparkles,
  Type,
} from 'lucide-react';
import ArtifactViewer from '../components/ArtifactViewer';
import SessionMenu from '../components/SessionMenu';
import { getLang, t } from '../i18n';
import { AuthUser } from '../services/auth';
import {
  backend,
  BriefRecord,
  classifyProjectMessage,
  fetchBrief,
  fetchChatHistory,
  fetchCodeArtifact,
  fetchFactsheet,
  fetchInsights,
  fetchPlan,
  fetchProjectHead,
  fetchVersionFile,
  fetchVersionTree,
  fetchVersions,
  getPreviewUrl,
  HttpError,
  InsightRecord,
  isAuthError,
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
  hasSession: boolean;
  authUser: AuthUser | null;
  onAuthError: () => void;
  onBack: () => void;
  onOpenSidebar: () => void;
  onOpenSettings: () => void;
  onNavigate: (href: string) => void;
  onSignOut: () => Promise<void> | void;
}

type ActiveTab = 'preview' | 'brief' | 'buildPlan' | 'code' | 'changes' | 'versions';
type RemoteState<T> = { loading: boolean; error: boolean; data: T | null };
type CodeFileRecord = { filename: string; content: string; language: string };
type InsightCategoryKey = 'detail' | 'color' | 'content' | 'typography' | 'domain' | 'default';
type InsightsState = { version: number | null; promptScore: number | null; insights: InsightRecord[] };

const EMPTY_REMOTE = { loading: false, error: false, data: null };

function createEmptyInsightsState(): InsightsState {
  return { version: null, promptScore: null, insights: [] };
}

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

function getLatestVersion(versions: VersionRecord[]): number | null {
  if (versions.length === 0) return null;
  return versions.reduce((latest, current) => (current.version > latest ? current.version : latest), versions[0].version);
}

function getInsightsCollapseStorageKey(projectId: string) {
  return `archon-insights-collapsed-${projectId}`;
}

function clampScore(score?: number | null): number | null {
  if (typeof score !== 'number' || Number.isNaN(score)) return null;
  return Math.max(0, Math.min(100, Math.round(score)));
}

function normalizeInsightPriority(priority: string): 'high' | 'medium' | 'low' {
  const value = String(priority || '').toLowerCase();
  if (value === 'high' || value === 'medium') return value;
  return 'low';
}

function resolveInsightCategoryKey(insight: InsightRecord): InsightCategoryKey {
  const category = String(insight.category || '').toLowerCase();
  const hint = `${category} ${insight.suggestion}`.toLowerCase();
  const mentionsTypography = /(font|typography|sans|serif|monospace|heading)/.test(hint);
  const mentionsColor = /(color|colour|palette|accent|theme|gradient)/.test(hint);

  if (category.includes('font') || category.includes('typography') || mentionsTypography) return 'typography';
  if (category.includes('color') || category.includes('palette') || (category === 'visual' && mentionsColor)) return 'color';
  if (category.includes('content') || category.includes('section')) return 'content';
  if (category.includes('domain')) return 'domain';
  if (category.includes('prompt_length') || category.includes('detail') || category.includes('clarity')) return 'detail';
  if (category === 'visual') return 'color';
  return 'default';
}

function getInsightCategoryLabel(lang: ReturnType<typeof getLang>, categoryKey: InsightCategoryKey) {
  if (categoryKey === 'detail' || categoryKey === 'default') return t(lang, 'insightCategoryDetail');
  if (categoryKey === 'color') return t(lang, 'insightCategoryColor');
  if (categoryKey === 'content') return t(lang, 'insightCategoryContent');
  if (categoryKey === 'typography') return t(lang, 'insightCategoryTypography');
  return t(lang, 'insightCategoryDomain');
}

function getInsightCategoryIcon(categoryKey: InsightCategoryKey) {
  if (categoryKey === 'detail') return AlignLeft;
  if (categoryKey === 'color') return Palette;
  if (categoryKey === 'content') return Layers3;
  if (categoryKey === 'typography') return Type;
  if (categoryKey === 'domain') return Globe2;
  return Lightbulb;
}

function getPriorityBadgeStyles(priority: 'high' | 'medium' | 'low') {
  if (priority === 'high') {
    return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/20 dark:bg-rose-500/10 dark:text-rose-200';
  }
  if (priority === 'medium') {
    return 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200';
  }
  return 'border-slate-200 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300';
}

function getPriorityLabel(lang: ReturnType<typeof getLang>, priority: 'high' | 'medium' | 'low') {
  if (priority === 'high') return t(lang, 'priorityHigh');
  if (priority === 'medium') return t(lang, 'priorityMedium');
  return t(lang, 'priorityLow');
}

function getScoreFillStyles(score: number) {
  if (score >= 70) return 'bg-emerald-500 dark:bg-emerald-400';
  if (score >= 40) return 'bg-amber-500 dark:bg-amber-400';
  return 'bg-rose-500 dark:bg-rose-400';
}

function buildIterationPromptHistory(
  originalPrompt: string,
  messages: PromptHistoryEntry[],
  userMessage: PromptHistoryEntry
): PromptHistoryEntry[] {
  const trimmedOriginalPrompt = originalPrompt.trim();
  const sanitized = [...messages, userMessage]
    .map(({ role, content }) => ({ role, content: content.trim() }))
    .filter((entry) => entry.content.length > 0);

  if (!trimmedOriginalPrompt) {
    return sanitized;
  }

  const withoutOriginalPrompt = sanitized.filter(
    (entry) => !(entry.role === 'user' && entry.content === trimmedOriginalPrompt)
  );

  return [{ role: 'user', content: trimmedOriginalPrompt }, ...withoutOriginalPrompt];
}

async function loadWithRetry<T>(loader: () => Promise<T>, retries = 0, delayMs = 700): Promise<T> {
  let attempt = 0;

  while (true) {
    try {
      return await loader();
    } catch (error) {
      if (attempt >= retries || isAuthError(error)) {
        throw error;
      }
      attempt += 1;
      await new Promise((resolve) => window.setTimeout(resolve, delayMs * attempt));
    }
  }
}

const EmptyPanel: React.FC<{ icon: React.ReactNode; title: string; detail?: string }> = ({ icon, title, detail }) => (
  <div className="flex min-h-[360px] flex-col items-center justify-center rounded-[2rem] border border-slate-200 bg-white px-6 text-center shadow-sm dark:border-white/10 dark:bg-[#111827]">
    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-600 dark:bg-white/5 dark:text-slate-200">{icon}</div>
    <h3 className="mt-5 text-lg font-semibold text-slate-950 dark:text-white">{title}</h3>
    {detail && <p className="mt-2 max-w-md text-sm leading-6 text-slate-500 dark:text-slate-300/70">{detail}</p>}
  </div>
);

interface BuildSkeletonScreenProps {
  currentStage?: string | null;
  archetype?: string | null;
}

const skeletonBlock = (className: string) => <div className={`archon-shimmer rounded-[1.25rem] ${className}`} />;

function renderLandingSkeleton() {
  return (
    <div className="space-y-4">
      {skeletonBlock('h-8 w-full rounded-2xl')}
      {skeletonBlock('h-48 w-full rounded-[1.5rem]')}
      <div className="grid gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="space-y-3 rounded-[1.5rem] border border-slate-200/60 p-4 dark:border-white/5">
            {skeletonBlock('h-20 w-full rounded-[1.25rem]')}
            {skeletonBlock('h-4 w-3/4')}
            {skeletonBlock('h-4 w-1/2')}
          </div>
        ))}
      </div>
      {skeletonBlock('h-16 w-full rounded-[1.5rem]')}
      {skeletonBlock('h-12 w-full rounded-2xl')}
    </div>
  );
}

function renderDashboardSkeleton() {
  return (
    <div className="space-y-4">
      {skeletonBlock('h-8 w-full rounded-2xl')}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="space-y-3 rounded-[1.5rem] border border-slate-200/60 p-4 dark:border-white/5">
            {skeletonBlock('h-6 w-2/5')}
            {skeletonBlock('h-8 w-3/5')}
          </div>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        {skeletonBlock('h-48 w-full rounded-[1.5rem]')}
        {skeletonBlock('h-48 w-full rounded-[1.5rem]')}
      </div>
      <div className="space-y-3 rounded-[1.5rem] border border-slate-200/60 p-4 dark:border-white/5">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className={`archon-shimmer h-8 rounded-xl ${index % 2 === 1 ? 'opacity-70' : ''}`} />
        ))}
      </div>
    </div>
  );
}

function renderEcommerceSkeleton() {
  return (
    <div className="space-y-4">
      {skeletonBlock('h-8 w-full rounded-2xl')}
      {skeletonBlock('h-32 w-full rounded-[1.5rem]')}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <div key={index} className="space-y-3 rounded-[1.5rem] border border-slate-200/60 p-4 dark:border-white/5">
            {skeletonBlock('h-24 w-full rounded-[1.25rem]')}
            {skeletonBlock('h-4 w-3/4')}
            {skeletonBlock('h-4 w-1/2')}
          </div>
        ))}
      </div>
    </div>
  );
}

function renderPortfolioSkeleton() {
  return (
    <div className="space-y-4">
      {skeletonBlock('h-8 w-full rounded-2xl')}
      <div className="flex items-center gap-4 rounded-[1.5rem] border border-slate-200/60 p-5 dark:border-white/5">
        <div className="archon-shimmer h-12 w-12 rounded-full" />
        <div className="flex-1 space-y-3">
          {skeletonBlock('h-4 w-2/5')}
          {skeletonBlock('h-4 w-3/5')}
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="space-y-3 rounded-[1.5rem] border border-slate-200/60 p-4 dark:border-white/5">
            {skeletonBlock('h-24 w-full rounded-[1.25rem]')}
            {skeletonBlock('h-4 w-2/3')}
            {skeletonBlock('h-4 w-1/2')}
          </div>
        ))}
      </div>
    </div>
  );
}

function renderGameSkeleton() {
  return (
    <div className="space-y-4">
      {skeletonBlock('h-56 w-full rounded-[1.75rem]')}
      <div className="grid gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="space-y-3 rounded-[1.5rem] border border-slate-200/60 p-4 dark:border-white/5">
            {skeletonBlock('h-16 w-full rounded-[1.25rem]')}
            {skeletonBlock('h-4 w-3/4')}
          </div>
        ))}
      </div>
      {skeletonBlock('h-20 w-full rounded-[1.5rem]')}
    </div>
  );
}

const BuildSkeletonScreen: React.FC<BuildSkeletonScreenProps> = ({ currentStage, archetype }) => {
  const normalizedArchetype = String(archetype || '').toLowerCase();
  const stageMessage =
    currentStage === 'pm'
      ? 'Understanding your idea...'
      : currentStage === 'planner'
        ? 'Planning your layout...'
        : currentStage === 'engineer'
          ? 'Writing your code...'
          : 'Building your app...';

  const skeleton =
    normalizedArchetype === 'landing' || normalizedArchetype === 'saas_landing'
      ? renderLandingSkeleton()
      : normalizedArchetype === 'dashboard'
        ? renderDashboardSkeleton()
        : normalizedArchetype === 'ecommerce'
          ? renderEcommerceSkeleton()
          : normalizedArchetype === 'portfolio'
            ? renderPortfolioSkeleton()
            : renderGameSkeleton();

  return (
    <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#111827]">
      <style>{`
        @keyframes archon-shimmer {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        .archon-shimmer {
          background: linear-gradient(90deg,
            rgba(148,163,184,0.12) 25%,
            rgba(148,163,184,0.28) 50%,
            rgba(148,163,184,0.12) 75%
          );
          background-size: 200% 100%;
          animation: archon-shimmer 1.8s linear infinite;
        }
        .dark .archon-shimmer {
          background: linear-gradient(90deg,
            rgba(255,255,255,0.04) 25%,
            rgba(255,255,255,0.10) 50%,
            rgba(255,255,255,0.04) 75%
          );
          background-size: 200% 100%;
          animation: archon-shimmer 1.8s linear infinite;
        }
      `}</style>
      <div className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-800">
        <div className="flex items-center gap-1.5">
          <div className="h-2 w-2 rounded-full bg-rose-400" />
          <div className="h-2 w-2 rounded-full bg-amber-400" />
          <div className="h-2 w-2 rounded-full bg-emerald-400" />
        </div>
        <div className="archon-shimmer h-5 w-32 rounded-full sm:w-48" />
        <div className="ml-auto flex items-center gap-2 text-right text-xs text-slate-500 dark:text-slate-300/70">
          <span
            className="inline-block text-sm text-slate-950 dark:text-white"
            style={{ animation: 'archon-shimmer 2s ease-in-out infinite' }}
          >
            ✦
          </span>
          <span>{stageMessage}</span>
        </div>
      </div>
      <div className="bg-slate-100 p-4 dark:bg-slate-900 sm:p-6">
        <div className="min-h-[70vh] rounded-b-[1.5rem] rounded-t-[1.5rem] bg-white p-4 shadow-sm dark:bg-slate-950/60 sm:p-6">
          {skeleton}
        </div>
      </div>
    </div>
  );
};

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

interface BuildInsightsCardProps {
  lang: ReturnType<typeof getLang>;
  version: number;
  insights: InsightRecord[];
  promptScore: number | null;
  collapsed: boolean;
  onToggleCollapse: () => void;
  onApplySuggestion: (suggestion: string) => void;
}

const BuildInsightsCard: React.FC<BuildInsightsCardProps> = ({
  lang,
  version,
  insights,
  promptScore,
  collapsed,
  onToggleCollapse,
  onApplySuggestion,
}) => {
  const score = clampScore(promptScore);
  const [isVisible, setIsVisible] = useState(false);
  const [animateBar, setAnimateBar] = useState(false);

  useEffect(() => {
    setIsVisible(false);
    setAnimateBar(false);

    const visibilityTimer = window.setTimeout(() => setIsVisible(true), 24);
    const barTimer = window.setTimeout(() => setAnimateBar(true), 180);

    return () => {
      window.clearTimeout(visibilityTimer);
      window.clearTimeout(barTimer);
    };
  }, [version]);

  return (
    <div
      className={`overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-[0_20px_50px_rgba(15,23,42,0.08)] transition-all duration-500 ease-out dark:border-white/10 dark:bg-[#111827] dark:shadow-[0_20px_50px_rgba(2,6,23,0.32)] ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200/80 bg-[linear-gradient(135deg,rgba(254,249,195,0.55),rgba(255,255,255,0.96),rgba(224,242,254,0.72))] px-5 py-4 dark:border-white/10 dark:bg-[linear-gradient(135deg,rgba(30,41,59,0.92),rgba(17,24,39,0.98),rgba(15,23,42,0.94))]">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-100 text-amber-600 dark:bg-amber-500/10 dark:text-amber-300">
            <Sparkles size={18} />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-950 dark:text-white">{t(lang, 'buildInsights')}</div>
            <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-400 dark:text-slate-300/60">v{version}</div>
          </div>
        </div>
        <button
          type="button"
          onClick={onToggleCollapse}
          className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-3 py-2 text-xs font-medium text-slate-600 transition hover:bg-white hover:text-slate-950 dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:hover:bg-white/10 dark:hover:text-white"
        >
          {t(lang, collapsed ? 'expand' : 'collapse')}
          <ChevronDown size={14} className={`transition-transform duration-300 ${collapsed ? '' : 'rotate-180'}`} />
        </button>
      </div>

      <div className={`overflow-hidden transition-all duration-300 ease-out ${collapsed ? 'max-h-0 opacity-0' : 'max-h-[1200px] opacity-100'}`}>
        <div className="grid gap-5 px-5 pb-5 pt-5 lg:grid-cols-[240px_minmax(0,1fr)]">
          <div className="rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-slate-950/40">
            <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-400 dark:text-slate-300/60">{t(lang, 'promptScore')}</div>
            <div className="mt-4 flex items-end gap-2">
              <span className="text-4xl font-semibold tracking-tight text-slate-950 dark:text-white">{score ?? '—'}</span>
              <span className="pb-1 text-sm text-slate-400 dark:text-slate-300/60">/100</span>
            </div>
            {score != null && (
              <div className="mt-5">
                <div className="flex items-center gap-3">
                  <div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-white/10">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ease-out ${getScoreFillStyles(score)}`}
                      style={{ width: animateBar ? `${score}%` : '0%' }}
                    />
                  </div>
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-200">{score}%</span>
                </div>
              </div>
            )}
          </div>

          <div>
            <div className="text-sm font-semibold text-slate-950 dark:text-white">{t(lang, 'insightsTipsTitle')}</div>
            <div className="mt-4 space-y-3">
              {insights.map((insight, index) => {
                const categoryKey = resolveInsightCategoryKey(insight);
                const Icon = getInsightCategoryIcon(categoryKey);
                const priority = normalizeInsightPriority(insight.priority);

                return (
                  <article
                    key={`${insight.category}-${index}-${insight.suggestion}`}
                    className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-white/5"
                  >
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="inline-flex h-9 w-9 items-center justify-center rounded-2xl bg-white text-slate-600 shadow-sm dark:bg-slate-950/70 dark:text-slate-100">
                            <Icon size={16} />
                          </span>
                          <span className="text-sm font-semibold text-slate-950 dark:text-white">
                            {getInsightCategoryLabel(lang, categoryKey)}
                          </span>
                          <span
                            className={`inline-flex items-center rounded-full border px-2 py-1 text-[11px] font-medium ${getPriorityBadgeStyles(priority)}`}
                          >
                            {getPriorityLabel(lang, priority)}
                          </span>
                        </div>
                        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-200/80">{insight.suggestion}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => onApplySuggestion(insight.suggestion)}
                        className="inline-flex w-full items-center justify-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-100 hover:text-slate-950 sm:w-auto dark:border-white/10 dark:bg-slate-950/40 dark:text-slate-100 dark:hover:bg-slate-950"
                      >
                        {t(lang, 'applySuggestion')}
                        <ArrowRight size={14} />
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const ProjectDetailPage: React.FC<ProjectDetailPageProps> = ({
  projectId,
  hasSession,
  authUser,
  onAuthError,
  onBack,
  onOpenSidebar,
  onOpenSettings,
  onNavigate,
  onSignOut,
}) => {
  const lang = getLang();
  const [project, setProject] = useState<Project | undefined>(undefined);
  const [activeTab, setActiveTab] = useState<ActiveTab>('preview');
  const [version, setVersion] = useState<number | null>(null);
  const [viewport, setViewport] = useState<'desktop' | 'mobile'>('desktop');
  const [messages, setMessages] = useState<PromptHistoryEntry[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [composerError, setComposerError] = useState<string | null>(null);
  const [versionsState, setVersionsState] = useState({
    loading: true,
    error: false,
    restoringId: null as string | null,
    selectedId: null as string | null,
    versions: [] as VersionRecord[],
  });
  const [briefState, setBriefState] = useState<RemoteState<BriefRecord>>(EMPTY_REMOTE);
  const [planState, setPlanState] = useState<RemoteState<Artifact>>(EMPTY_REMOTE);
  const [changesState, setChangesState] = useState<RemoteState<EngineerTask[]>>(EMPTY_REMOTE);
  const [headError, setHeadError] = useState(false);
  const [previewRefreshKey, setPreviewRefreshKey] = useState(() => Date.now());
  const [showRegisterPrompt, setShowRegisterPrompt] = useState(false);
  const [insightsState, setInsightsState] = useState<InsightsState>(() => createEmptyInsightsState());
  const [insightsCollapsed, setInsightsCollapsed] = useState(() => {
    if (typeof window === 'undefined') return false;
    return localStorage.getItem(getInsightsCollapseStorageKey(projectId)) === '1';
  });
  const chatTextareaRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const previousStatusRef = useRef<Project['status'] | null>(null);
  const previousPreviewVersionRef = useRef<number | null>(null);

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
        const versions = [...(await fetchVersions(projectId))].sort((left, right) => right.version - left.version);
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

  const latestVersion = useMemo(() => getLatestVersion(versionsState.versions), [versionsState.versions]);
  const resolvedVersion = version ?? latestVersion;
  const previewSrc = resolvedVersion ? `${getPreviewUrl(projectId, resolvedVersion)}?refresh=${previewRefreshKey}` : null;

  useEffect(() => {
    if (version == null && latestVersion != null) {
      setVersion(latestVersion);
      setHeadError(false);
    }
  }, [latestVersion, version]);

  useEffect(() => {
    const previousStatus = previousStatusRef.current;

    if (project?.status === 'COMPLETED' && previousStatus === 'RUNNING') {
      if (latestVersion != null) {
        setVersion(latestVersion);
        setHeadError(false);
      }
      setPreviewRefreshKey(Date.now());
      if (!localStorage.getItem('archon_token')) {
        setShowRegisterPrompt(true);
      }
    }

    previousStatusRef.current = project?.status ?? null;
  }, [latestVersion, project?.status]);

  useEffect(() => {
    if (hasSession && showRegisterPrompt) {
      setShowRegisterPrompt(false);
    }
  }, [hasSession, showRegisterPrompt]);

  useEffect(() => {
    if (!resolvedVersion) return;
    if (previousPreviewVersionRef.current === resolvedVersion) return;

    previousPreviewVersionRef.current = resolvedVersion;
    setPreviewRefreshKey(Date.now());
  }, [resolvedVersion]);

  useEffect(() => {
    setInsightsCollapsed(typeof window !== 'undefined' && localStorage.getItem(getInsightsCollapseStorageKey(projectId)) === '1');
  }, [projectId]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    localStorage.setItem(getInsightsCollapseStorageKey(projectId), insightsCollapsed ? '1' : '0');
  }, [insightsCollapsed, projectId]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      if (project?.status !== 'COMPLETED' || resolvedVersion == null || versionsState.loading) {
        if (!cancelled) setInsightsState(createEmptyInsightsState());
        return;
      }

      const retries = 2;
      const [insightsResult, factsheetResult] = await Promise.allSettled([
        loadWithRetry(() => fetchInsights(projectId, resolvedVersion), retries),
        loadWithRetry(() => fetchFactsheet(projectId, resolvedVersion), retries),
      ]);

      if (cancelled) return;

      if (insightsResult.status !== 'fulfilled' || insightsResult.value.length === 0) {
        setInsightsState(createEmptyInsightsState());
        return;
      }

      const promptScore =
        factsheetResult.status === 'fulfilled'
          ? clampScore(factsheetResult.value.scoring?.prompt_quality?.score ?? null)
          : null;

      setInsightsState({
        version: resolvedVersion,
        promptScore,
        insights: insightsResult.value.slice(0, 4),
      });
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, [project?.status, projectId, resolvedVersion, versionsState.loading]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      if (!resolvedVersion) {
        const hasVersionError = headError && latestVersion == null;
        setBriefState({ loading: false, error: hasVersionError, data: null });
        setPlanState({ loading: false, error: hasVersionError, data: null });
        setChangesState({ loading: false, error: hasVersionError, data: null });
        return;
      }

      setBriefState({ loading: true, error: false, data: null });
      setPlanState({ loading: true, error: false, data: null });
      setChangesState({ loading: true, error: false, data: null });

      const retries = project?.status === 'COMPLETED' ? 2 : 0;
      const [brief, plan, code] = await Promise.allSettled([
        loadWithRetry(() => fetchBrief(projectId, resolvedVersion), retries),
        loadWithRetry(() => fetchPlan(projectId, resolvedVersion), retries),
        loadWithRetry(() => fetchCodeArtifact(projectId, resolvedVersion), retries),
      ]);
      if (cancelled) return;

      const authFailure = [brief, plan, code].find(
        (result) => result.status === 'rejected' && isAuthError(result.reason)
      );
      if (authFailure) {
        onAuthError();
      }

      const treatAsPending = (result: PromiseSettledResult<unknown>) =>
        result.status === 'rejected' &&
        result.reason instanceof HttpError &&
        result.reason.status === 404 &&
        project?.status !== 'COMPLETED';

      setBriefState(
        brief.status === 'fulfilled'
          ? { loading: false, error: false, data: brief.value }
          : treatAsPending(brief)
          ? { loading: false, error: false, data: null }
          : { loading: false, error: true, data: null }
      );
      setPlanState(
        plan.status === 'fulfilled'
          ? {
              loading: false,
              error: false,
              data: {
                id: `plan-${projectId}-${resolvedVersion}`,
                projectId,
                type: 'PLAN',
                title: t(lang, 'buildPlan'),
                content: plan.value,
                createdAt: Date.now(),
                agent: 'Archon',
              },
            }
          : treatAsPending(plan)
          ? { loading: false, error: false, data: null }
          : { loading: false, error: true, data: null }
      );
      setChangesState(
        code.status === 'fulfilled'
          ? { loading: false, error: false, data: code.value.tasks }
          : treatAsPending(code)
          ? { loading: false, error: false, data: [] }
          : { loading: false, error: true, data: null }
      );
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [project?.status, projectId, resolvedVersion, latestVersion, lang, headError, onAuthError]);

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
    const promptHistory = buildIterationPromptHistory(project.description || project.name, messages, userMessage);

    setMessages(nextMessages);
    setChatInput('');
    setChatLoading(true);
    setComposerError(null);

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
        await backend.startIteration(projectId, userMessage.content, promptHistory);
      }
    } catch (error) {
      setMessages((current) => {
        if (current[current.length - 1]?.timestamp === userMessage.timestamp) {
          return current.slice(0, -1);
        }
        return current;
      });
      if (isAuthError(error)) {
        setComposerError(t(lang, 'authRequiredBody'));
        onAuthError();
      } else if (isNetworkError(error)) {
        setComposerError(t(lang, 'backendRequired'));
      } else {
        setComposerError(t(lang, 'couldNotLoad'));
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

  const handleApplySuggestion = (suggestion: string) => {
    setChatInput(suggestion);
    setComposerError(null);
    window.setTimeout(() => {
      chatTextareaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      chatTextareaRef.current?.focus();
      chatTextareaRef.current?.setSelectionRange(suggestion.length, suggestion.length);
    }, 0);
  };

  if (!project) {
    return (
      <div className="flex h-full items-center justify-center bg-[var(--app-bg)] text-sm text-slate-500 dark:text-slate-300">
        <Loader2 size={18} className="mr-2 animate-spin" />
        {t(lang, 'sending')}
      </div>
    );
  }

  const signInHref = `/login?guest_project_id=${encodeURIComponent(projectId)}`;

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
            <SessionMenu
              hasSession={hasSession}
              user={authUser}
              signInHref={signInHref}
              onNavigate={onNavigate}
              onSignOut={onSignOut}
            />
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
              {composerError && (
                <div className="mb-3 rounded-[1.25rem] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-100">
                  {composerError}
                </div>
              )}
              <textarea
                ref={chatTextareaRef}
                value={chatInput}
                onChange={(event) => {
                  setChatInput(event.target.value);
                  if (composerError) {
                    setComposerError(null);
                  }
                }}
                onKeyDown={(event) => {
                  if (event.key !== 'Enter' || event.shiftKey) return;
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }}
                disabled={chatLoading || project.status === 'RUNNING'}
                placeholder={
                  project.status === 'RUNNING'
                    ? t(lang, 'buildInProgress')
                    : t(lang, 'chatComposerPlaceholder')
                }
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

        <section className="custom-scrollbar order-1 space-y-4 overflow-y-auto lg:order-2">
          {activeTab === 'preview' &&
            (resolvedVersion && previewSrc ? (
              <div className="overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-sm dark:border-white/10 dark:bg-[#111827]">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-white/10">
                  <div>
                    <div className="text-sm font-semibold text-slate-950 dark:text-white">{t(lang, 'latestVersion')}</div>
                    <div className="mt-1 text-sm text-slate-500 dark:text-slate-300/70">
                      {t(lang, 'versionHistory')} {resolvedVersion}
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
                    <iframe title="Project preview" src={previewSrc} className="h-[70vh] w-full rounded-[1.5rem] border-0 bg-white shadow-sm" />
                  ) : (
                    <div className="mx-auto w-[375px] max-w-full overflow-hidden rounded-[2.25rem] border-[10px] border-slate-950 bg-white shadow-2xl dark:border-slate-200">
                      <iframe title="Project preview mobile" src={previewSrc} className="h-[70vh] w-full border-0 bg-white" />
                    </div>
                  )}
                </div>
              </div>
            ) : project?.status === 'RUNNING' ? (
              <BuildSkeletonScreen currentStage={project.currentStage} archetype={project.uiArchetype} />
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
                    <h3 className="text-sm font-semibold text-slate-950 dark:text-white">{t(lang, 'briefGoals')}</h3>
                    <ul className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-200/80">
                      {(
                        briefState.data.goals.length > 0 ? briefState.data.goals : briefState.data.userStories
                      ).map((item: string) => (
                        <li key={item} className="rounded-2xl bg-white px-4 py-3 dark:bg-slate-950/40">
                          {item}
                        </li>
                      ))}
                    </ul>
                  </section>
                </div>
                {briefState.data.targetUsers?.length > 0 && (
                  <section className="mt-6 rounded-[1.75rem] border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-white/5">
                    <h3 className="text-sm font-semibold text-slate-950 dark:text-white">{t(lang, 'briefAudience')}</h3>
                    <ul className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-200/80">
                      {briefState.data.targetUsers.map((user: string) => (
                        <li key={user} className="rounded-2xl bg-white px-4 py-3 dark:bg-slate-950/40">
                          {user}
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
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

          {activeTab === 'code' && <CodePanel lang={lang} projectId={projectId} version={resolvedVersion} />}

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
              <EmptyPanel icon={<History size={22} />} title={t(lang, 'noChangesYet')} />
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

          {insightsState.version != null && insightsState.insights.length > 0 && (
            <BuildInsightsCard
              key={`${projectId}-${insightsState.version}`}
              lang={lang}
              version={insightsState.version}
              insights={insightsState.insights}
              promptScore={insightsState.promptScore}
              collapsed={insightsCollapsed}
              onToggleCollapse={() => setInsightsCollapsed((current) => !current)}
              onApplySuggestion={handleApplySuggestion}
            />
          )}
        </section>
      </div>

      {showRegisterPrompt && !hasSession && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/30 p-4 backdrop-blur-sm sm:items-center">
          <div className="w-full max-w-lg rounded-[2rem] border border-white/80 bg-white p-6 shadow-[0_30px_80px_rgba(15,23,42,0.16)] sm:p-7">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium uppercase tracking-[0.18em] text-emerald-700">
              <Sparkles size={14} />
              Build Ready
            </div>
            <h3 className="mt-4 text-2xl font-semibold tracking-tight text-slate-950">
              Your app is ready! Create a free account to save it and keep building.
            </h3>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              You can keep reviewing this version right now. Create an account whenever you want to save this project and keep iterating from it.
            </p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => onNavigate(`/register?guest_project_id=${encodeURIComponent(projectId)}`)}
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-[1.25rem] bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
              >
                Create Account
                <ExternalLink size={16} />
              </button>
              <button
                type="button"
                onClick={() => setShowRegisterPrompt(false)}
                className="inline-flex flex-1 items-center justify-center rounded-[1.25rem] border border-slate-200 px-4 py-3 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
              >
                Maybe Later
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDetailPage;
