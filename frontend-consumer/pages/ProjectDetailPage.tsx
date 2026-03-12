import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  ChevronDown,
  Clock3,
  Code2,
  ExternalLink,
  FileCode2,
  FileText,
  History,
  Layers3,
  Lightbulb,
  Loader2,
  Menu,
  Monitor,
  RefreshCw,
  RotateCcw,
  SendHorizontal,
  Settings2,
  Smartphone,
  Sparkles,
} from 'lucide-react';
import ArtifactViewer from '../components/ArtifactViewer';
import SessionMenu from '../components/SessionMenu';
import { t, type Lang } from '../i18n';
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
  lang: Lang;
  hasSession: boolean;
  authUser: AuthUser | null;
  onAuthError: () => void;
  onBack: () => void;
  onOpenSidebar: () => void;
  onOpenSettings: () => void;
  onNavigate: (href: string) => void;
  onSignOut: () => Promise<void> | void;
}

type ActiveTab = 'preview' | 'brief' | 'buildPlan' | 'code' | 'changes' | 'versions' | 'insights';
type RemoteState<T> = { loading: boolean; error: boolean; data: T | null };
type CodeFileRecord = { filename: string; content: string; language: string };
type InsightCategoryKey = 'detail' | 'color' | 'content' | 'default';
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

function getStatusLabel(project: Project, lang: Lang) {
  if (project.status === 'COMPLETED') return t(lang, 'statusCompleted');
  if (project.status === 'FAILED') return t(lang, 'statusFailed');
  if (project.status === 'RUNNING') return t(lang, 'statusRunning');
  return t(lang, 'statusIdle');
}

function getStatusTone(status: Project['status']) {
  if (status === 'COMPLETED') return { color: '#34d399', glow: 'rgba(52,211,153,0.45)' };
  if (status === 'FAILED') return { color: '#fb7185', glow: 'rgba(251,113,133,0.38)' };
  if (status === 'RUNNING') return { color: '#818cf8', glow: 'rgba(129,140,248,0.46)' };
  return { color: '#94a3b8', glow: 'rgba(148,163,184,0.3)' };
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
  const value = `${insight.category} ${insight.suggestion}`.toLowerCase();
  if (/(color|colour|palette|theme|gradient|visual)/.test(value)) return 'color';
  if (/(content|section|copy|story)/.test(value)) return 'content';
  if (/(detail|clarity|specific|prompt)/.test(value)) return 'detail';
  return 'default';
}

function getInsightCategoryLabel(lang: Lang, categoryKey: InsightCategoryKey) {
  if (categoryKey === 'color') return t(lang, 'insightCategoryColor');
  if (categoryKey === 'content') return t(lang, 'insightCategoryContent');
  return t(lang, 'insightCategoryDetail');
}

function getPriorityBadge(priority: 'high' | 'medium' | 'low') {
  if (priority === 'high') return 'border-rose-400/30 bg-rose-500/10 text-rose-100';
  if (priority === 'medium') return 'border-amber-400/30 bg-amber-500/10 text-amber-100';
  return 'border-white/10 bg-white/[0.04] text-white/68';
}

function getPriorityLabel(lang: Lang, priority: 'high' | 'medium' | 'low') {
  if (priority === 'high') return t(lang, 'priorityHigh');
  if (priority === 'medium') return t(lang, 'priorityMedium');
  return t(lang, 'priorityLow');
}

function buildInsightPrompt(suggestion: string): string {
  const lower = suggestion.toLowerCase();
  if (/(color|colour|palette|theme|gradient)/.test(lower)) {
    const m = suggestion.match(/like ['"](.+?)['"]/);
    return m ? `Use ${m[1]} as the color scheme` : `Add a color scheme - try dark theme with vibrant accents`;
  }
  if (/(font|typography|typeface)/.test(lower)) return `Use more distinctive typography that matches the app's style`;
  if (/(section|layout|hero|navigation)/.test(lower)) {
    const m = suggestion.match(/like:\s*([^.]+)/s);
    return m ? `Add these sections: ${m[1].trim()}` : `Add all key sections to the layout`;
  }
  if (/(game|character|genre)/.test(lower)) return `Add the game title, genre, main characters, and what fans should see`;
  if (/(specific|detail|name|data|number)/.test(lower)) return `Add specific content - realistic names, numbers, and data throughout`;
  if (/(product|store|price|shop)/.test(lower)) return `Add product names, prices, descriptions, and categories`;
  if (/(portfolio|skill|project)/.test(lower)) return `Add my name, role, skills, and portfolio projects`;
  if (/(clarity|structure|short)/.test(lower)) return `Improve the overall structure and content quality`;
  const first = suggestion.split('.')[0].replace(/^(Your prompt[^.]*\.\s*|You didn't[^.]*\.\s*|Try )/i, '');
  return first.length > 8 ? first : `Improve this app`;
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
  <div className="flex min-h-[340px] flex-col items-center justify-center rounded-[2rem] border border-white/10 bg-[#07101f] px-6 text-center shadow-[0_24px_80px_rgba(2,6,23,0.34)]">
    <div className="flex h-14 w-14 items-center justify-center rounded-[1.35rem] bg-white/[0.05] text-indigo-200">{icon}</div>
    <h3 className="mt-5 text-lg font-semibold text-white">{title}</h3>
    {detail && <p className="mt-2 max-w-md text-sm leading-6 text-white/50">{detail}</p>}
  </div>
);

const ChatBubble: React.FC<{ message: PromptHistoryEntry }> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[88%] rounded-[1.4rem] px-4 py-3 text-sm leading-6 shadow-[0_16px_40px_rgba(2,6,23,0.2)] ${
          isUser
            ? 'bg-[linear-gradient(135deg,#4f46e5,#7c3aed)] text-white'
            : 'border border-white/10 bg-white/[0.06] text-white/78 backdrop-blur-xl'
        }`}
      >
        <div>{message.content}</div>
        {message.timestamp && <div className="mt-2 text-[11px] uppercase tracking-[0.18em] opacity-60">{formatTimestamp(message.timestamp)}</div>}
      </div>
    </div>
  );
};

const NeuralBuildScreen: React.FC<{ message: string; stage?: string | null }> = ({ message, stage }) => (
  <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#07101f] p-6 shadow-[0_24px_80px_rgba(2,6,23,0.34)]">
    <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(79,70,229,0.18),transparent_52%),radial-gradient(circle_at_bottom_right,rgba(8,145,178,0.14),transparent_46%)]" />
    <div className="relative">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.26em] text-white/42">{stage || 'Build'}</div>
          <div className="mt-2 text-lg font-semibold text-white">{message}</div>
        </div>
        <div className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs uppercase tracking-[0.22em] text-white/54">
          Live
        </div>
      </div>
      <div className="relative h-[70vh] min-h-[420px] overflow-hidden rounded-[1.8rem] border border-white/10 bg-[#03050f]">
        <div className="neural-line absolute left-[18%] top-[24%] h-px w-[26%] origin-left rotate-[14deg] bg-gradient-to-r from-transparent via-indigo-300/80 to-transparent" />
        <div className="neural-line absolute left-[38%] top-[30%] h-px w-[24%] origin-left rotate-[-12deg] bg-gradient-to-r from-transparent via-cyan-300/80 to-transparent" />
        <div className="neural-line absolute left-[26%] top-[54%] h-px w-[30%] origin-left rotate-[-8deg] bg-gradient-to-r from-transparent via-violet-300/80 to-transparent" />
        <div className="neural-line absolute left-[52%] top-[52%] h-px w-[18%] origin-left rotate-[22deg] bg-gradient-to-r from-transparent via-indigo-300/80 to-transparent" />
        <div className="neural-line absolute left-[34%] top-[42%] h-px w-[18%] origin-left rotate-[75deg] bg-gradient-to-r from-transparent via-cyan-300/80 to-transparent" />
        <div className="neural-line absolute left-[58%] top-[34%] h-px w-[12%] origin-left rotate-[82deg] bg-gradient-to-r from-transparent via-violet-300/80 to-transparent" />
        {[
          ['18%', '24%'],
          ['40%', '30%'],
          ['62%', '24%'],
          ['26%', '54%'],
          ['50%', '46%'],
          ['70%', '58%'],
        ].map(([left, top], index) => (
          <span
            key={`${left}-${top}`}
            className="neural-node absolute h-4 w-4 rounded-full"
            style={{
              left,
              top,
              animationDelay: `${index * 0.22}s`,
              background:
                index % 3 === 0 ? '#4f46e5' : index % 3 === 1 ? '#7c3aed' : '#0891b2',
            }}
          />
        ))}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.04),transparent_55%)]" />
      </div>
    </div>
  </div>
);

const CodePanel: React.FC<{ lang: Lang; projectId: string; version: number | null; isBuilding: boolean }> = ({
  lang,
  projectId,
  version,
  isBuilding,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [files, setFiles] = useState<CodeFileRecord[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const codePanelRef = useRef<HTMLPreElement>(null);

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

  if (!version) {
    return isBuilding ? (
      <EmptyPanel
        icon={<RefreshCw size={22} />}
        title="Building..."
        detail="This will be ready when the build completes."
      />
    ) : (
      <EmptyPanel icon={<Code2 size={22} />} title={t(lang, 'noCodeYet')} />
    );
  }
  if (loading) return <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'sending')} />;
  if (error) {
    return isBuilding ? (
      <EmptyPanel
        icon={<RefreshCw size={22} />}
        title="Building..."
        detail="This will be ready when the build completes."
      />
    ) : (
      <EmptyPanel icon={<RefreshCw size={22} />} title={t(lang, 'couldNotLoad')} />
    );
  }
  if (files.length === 0) {
    return isBuilding ? (
      <EmptyPanel
        icon={<RefreshCw size={22} />}
        title="Building..."
        detail="This will be ready when the build completes."
      />
    ) : (
      <EmptyPanel icon={<Code2 size={22} />} title={t(lang, 'noCodeYet')} />
    );
  }

  return (
    <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-[#07101f] shadow-[0_24px_80px_rgba(2,6,23,0.34)]">
      <div className="grid min-h-[560px] lg:grid-cols-[270px_minmax(0,1fr)]">
        <aside className="border-b border-white/10 bg-white/[0.03] p-4 lg:border-b-0 lg:border-r">
          <div className="mb-4 flex items-center gap-2 text-xs uppercase tracking-[0.26em] text-white/38">
            <FileCode2 size={14} />
            {t(lang, 'files')}
          </div>
          <div className="custom-scrollbar max-h-[520px] space-y-2 overflow-y-auto pr-1">
            {files.map((file) => (
              <button
                key={file.filename}
                type="button"
                onClick={() => {
                  setSelected(file.filename);
                  codePanelRef.current?.scrollTo({ top: 0 });
                }}
                className={`block w-full rounded-[1.2rem] px-3 py-2 text-left text-sm transition ${
                  selected === file.filename
                    ? 'bg-[linear-gradient(135deg,rgba(79,70,229,0.3),rgba(124,58,237,0.18))] text-white'
                    : 'bg-white/[0.03] text-white/62 hover:bg-white/[0.06] hover:text-white'
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
              <div className="border-b border-white/10 px-5 py-4">
                <div className="text-sm font-semibold text-white">{activeFile.filename}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.22em] text-white/38">{activeFile.language}</div>
              </div>
              <pre ref={codePanelRef} className="custom-scrollbar max-h-[520px] overflow-auto p-5 text-sm leading-7 text-white/78">
                {activeFile.content}
              </pre>
            </>
          ) : (
            <EmptyPanel icon={<FileCode2 size={22} />} title={t(lang, 'selectFile')} />
          )}
        </div>
      </div>
    </div>
  );
};

interface BuildInsightsCardProps {
  lang: Lang;
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
  const [displayScore, setDisplayScore] = useState(0);
  const [visible, setVisible] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setVisible(false);
    setDisplayScore(0);

    const node = rootRef.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
        }
      },
      { threshold: 0.35 }
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, [version]);

  useEffect(() => {
    if (!visible || score == null) return;

    let frame = 0;
    const start = performance.now();
    const duration = 900;

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / duration);
      setDisplayScore(Math.round(score * progress));
      if (progress < 1) {
        frame = window.requestAnimationFrame(tick);
      }
    };

    frame = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(frame);
  }, [score, visible]);

  const circumference = 2 * Math.PI * 44;
  const dashoffset = score == null ? circumference : circumference - (circumference * displayScore) / 100;

  return (
    <div ref={rootRef} className="overflow-hidden rounded-[2rem] border border-white/10 bg-[#07101f] shadow-[0_24px_80px_rgba(2,6,23,0.34)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-[linear-gradient(135deg,rgba(79,70,229,0.18),rgba(124,58,237,0.12),rgba(8,145,178,0.14))] px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-[1.2rem] bg-white/[0.08] text-indigo-200">
            <Sparkles size={18} />
          </div>
          <div>
            <div className="text-sm font-semibold text-white">{t(lang, 'buildInsights')}</div>
            <div className="mt-1 text-xs uppercase tracking-[0.2em] text-white/40">v{version}</div>
          </div>
        </div>
        <button
          type="button"
          onClick={onToggleCollapse}
          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-medium text-white/70 transition hover:bg-white/[0.08] hover:text-white"
        >
          {collapsed ? 'Expand tips' : 'Collapse tips'}
          <ChevronDown size={14} className={`transition-transform duration-300 ${collapsed ? '' : 'rotate-180'}`} />
        </button>
      </div>

      <div className="grid gap-5 px-5 py-5 lg:grid-cols-[240px_minmax(0,1fr)]">
          <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.04] p-5">
            <div className="text-xs uppercase tracking-[0.24em] text-white/38">{t(lang, 'promptScore')}</div>
            <div className="mt-5 flex items-center justify-center">
              <div className="relative h-32 w-32">
                <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
                  <circle cx="60" cy="60" r="44" stroke="rgba(255,255,255,0.08)" strokeWidth="10" fill="none" />
                  <circle
                    cx="60"
                    cy="60"
                    r="44"
                    stroke="url(#score-ring)"
                    strokeWidth="10"
                    strokeLinecap="round"
                    fill="none"
                    strokeDasharray={circumference}
                    strokeDashoffset={dashoffset}
                    style={{ transition: 'stroke-dashoffset 220ms ease-out' }}
                  />
                  <defs>
                    <linearGradient id="score-ring" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="#4f46e5" />
                      <stop offset="50%" stopColor="#7c3aed" />
                      <stop offset="100%" stopColor="#0891b2" />
                    </linearGradient>
                  </defs>
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="text-3xl font-semibold text-white">{score == null ? '—' : displayScore}</div>
                  <div className="text-xs uppercase tracking-[0.2em] text-white/36">/100</div>
                </div>
              </div>
            </div>
          </div>

          <div>
            <div className="text-sm font-semibold text-white">{t(lang, 'insightsTipsTitle')}</div>
            <div className="mt-4 space-y-3">
              {insights.map((insight, index) => {
                const categoryKey = resolveInsightCategoryKey(insight);
                const priority = normalizeInsightPriority(insight.priority);
                return (
                  <article key={`${insight.category}-${index}-${insight.suggestion}`} className="rounded-[1.45rem] border border-white/10 bg-white/[0.04] p-4">
                    <div className="mb-3 flex flex-wrap items-center gap-2">
                      <span className="inline-flex h-9 w-9 items-center justify-center rounded-[1rem] bg-white/[0.07] text-indigo-200">
                        <Lightbulb size={16} />
                      </span>
                      <span className="text-sm font-semibold text-white">{getInsightCategoryLabel(lang, categoryKey)}</span>
                      <span className={`inline-flex rounded-full border px-2 py-1 text-[11px] font-medium ${getPriorityBadge(priority)}`}>
                        {getPriorityLabel(lang, priority)}
                      </span>
                    </div>

                    {!collapsed && (
                      <p className="mb-4 text-sm leading-6 text-white/60">{insight.suggestion}</p>
                    )}

                    <div className="flex items-center justify-between gap-3 rounded-[1.1rem] border border-indigo-400/15 bg-indigo-500/[0.07] px-4 py-3">
                      <div className="min-w-0">
                        <div className="mb-1 text-[11px] uppercase tracking-[0.2em] text-indigo-300/60">Try asking</div>
                        <div className="text-sm italic text-white/80">"{buildInsightPrompt(insight.suggestion)}"</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => onApplySuggestion(buildInsightPrompt(insight.suggestion))}
                        className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-full border border-indigo-400/25 bg-indigo-500/15 px-3 py-2 text-xs font-medium text-indigo-200 transition hover:bg-indigo-500/30 hover:text-white"
                      >
                        Use this
                        <ArrowRight size={13} />
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
        </div>
      </div>
    </div>
  );
};

const ProjectDetailPage: React.FC<ProjectDetailPageProps> = ({
  projectId,
  lang,
  hasSession,
  authUser,
  onAuthError,
  onBack,
  onOpenSidebar,
  onOpenSettings,
  onNavigate,
  onSignOut,
}) => {
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
  const [insightsUnread, setInsightsUnread] = useState(false);
  const [insightsCollapsed, setInsightsCollapsed] = useState(() => {
    if (typeof window === 'undefined') return false;
    const stored = localStorage.getItem(getInsightsCollapseStorageKey(projectId));
    return stored === null ? true : stored === '1';
  });
  const chatTextareaRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const rightPanelRef = useRef<HTMLElement>(null);
  const previousStatusRef = useRef<Project['status'] | null>(null);
  const previousPreviewVersionRef = useRef<number | null>(null);
  const previousInsightsVersionRef = useRef<number | null>(null);

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
            selectedId:
              current.selectedId && versions.some((item) => item.id === current.selectedId)
                ? current.selectedId
                : versions[0]?.id || null,
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
    if (insightsState.version == null || insightsState.insights.length === 0) {
      previousInsightsVersionRef.current = null;
      setInsightsUnread(false);
      return;
    }

    if (previousInsightsVersionRef.current !== insightsState.version) {
      previousInsightsVersionRef.current = insightsState.version;
      setInsightsUnread(activeTab !== 'insights');
    }
  }, [activeTab, insightsState.insights.length, insightsState.version]);

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
    { id: 'insights' as const, label: t(lang, 'buildInsights'), icon: Lightbulb },
  ];

  const handleTabChange = (tab: ActiveTab) => {
    if (tab === 'insights') {
      setInsightsUnread(false);
    }
    setActiveTab(tab);
    rightPanelRef.current?.scrollTo({ top: 0 });
  };

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
        handleTabChange('preview');
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
      handleTabChange('preview');
    } catch (error) {
      console.error('Failed to restore version', error);
      setVersionsState((current) => ({ ...current, restoringId: null }));
    }
  };

  const handleApplySuggestion = (prompt: string) => {
    setChatInput(prompt);
    setComposerError(null);
    window.setTimeout(() => {
      chatTextareaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      chatTextareaRef.current?.focus();
      chatTextareaRef.current?.setSelectionRange(prompt.length, prompt.length);
    }, 0);
  };

  if (!project) {
    return (
      <div className="flex h-full items-center justify-center bg-[#03050f] text-sm text-white/60">
        <Loader2 size={18} className="mr-2 animate-spin" />
        {t(lang, 'sending')}
      </div>
    );
  }

  const signInHref = `/login?guest_project_id=${encodeURIComponent(projectId)}`;
  const tone = getStatusTone(project.status);
  const isBuilding = project.status === 'RUNNING';

  let activePanel: React.ReactNode;

  if (activeTab === 'preview') {
    activePanel =
      project.status === 'RUNNING' ? (
        <NeuralBuildScreen message={statusMessage} stage={project.currentStage} />
      ) : resolvedVersion && previewSrc ? (
        <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-[#07101f] shadow-[0_24px_80px_rgba(2,6,23,0.34)]">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
            <div>
              <div className="text-sm font-semibold text-white">{t(lang, 'latestVersion')}</div>
              <div className="mt-1 text-xs uppercase tracking-[0.22em] text-white/38">
                {t(lang, 'versionHistory')} {resolvedVersion}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setViewport('desktop')}
                className={`rounded-full border px-3 py-2 transition ${
                  viewport === 'desktop'
                    ? 'border-indigo-400/40 bg-indigo-500/20 text-white'
                    : 'border-white/10 bg-white/[0.04] text-white/60 hover:bg-white/[0.08] hover:text-white'
                }`}
                aria-label="Desktop preview"
              >
                <Monitor size={16} />
              </button>
              <button
                type="button"
                onClick={() => setViewport('mobile')}
                className={`rounded-full border px-3 py-2 transition ${
                  viewport === 'mobile'
                    ? 'border-indigo-400/40 bg-indigo-500/20 text-white'
                    : 'border-white/10 bg-white/[0.04] text-white/60 hover:bg-white/[0.08] hover:text-white'
                }`}
                aria-label="Mobile preview"
              >
                <Smartphone size={16} />
              </button>
            </div>
          </div>
          <div className="bg-[#03050f] p-4 sm:p-6">
            {viewport === 'desktop' ? (
              <iframe title="Project preview" src={previewSrc} className="h-[72vh] w-full rounded-[1.5rem] border-0 bg-white" />
            ) : (
              <div className="mx-auto w-[390px] max-w-full overflow-hidden rounded-[2.2rem] border-[10px] border-slate-950 bg-white shadow-[0_24px_80px_rgba(2,6,23,0.45)]">
                <iframe title="Project preview mobile" src={previewSrc} className="h-[72vh] w-full border-0 bg-white" />
              </div>
            )}
          </div>
        </div>
      ) : (
        <EmptyPanel
          icon={<Monitor size={22} />}
          title={headError ? t(lang, 'couldNotLoad') : t(lang, 'noPreviewYet')}
          detail={headError ? undefined : t(lang, 'savedVersionsHint')}
        />
      );
  } else if (activeTab === 'brief') {
    activePanel = briefState.loading ? (
      <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'sending')} />
    ) : briefState.error ? (
      <EmptyPanel
        icon={<RefreshCw size={22} />}
        title={isBuilding ? 'Building...' : t(lang, 'couldNotLoad')}
        detail={isBuilding ? 'This will be ready when the build completes.' : undefined}
      />
    ) : briefState.data ? (
      <div className="rounded-[2rem] border border-white/10 bg-[#07101f] p-6 shadow-[0_24px_80px_rgba(2,6,23,0.34)] sm:p-8">
        <div className="inline-flex rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[11px] uppercase tracking-[0.22em] text-white/40">
          {t(lang, 'brief')}
        </div>
        <h2 className="mt-5 text-3xl font-semibold tracking-tight text-white">{briefState.data.title}</h2>
        <p className="mt-4 max-w-3xl text-base leading-7 text-white/58">{briefState.data.summary}</p>
        <div className="mt-8 grid gap-5 lg:grid-cols-2">
          <section className="rounded-[1.7rem] border border-white/10 bg-white/[0.04] p-5">
            <h3 className="text-sm font-semibold text-white">{t(lang, 'brief')}</h3>
            <div className="mt-4 space-y-3">
              {(briefState.data.features || []).map((feature) => (
                <div key={feature} className="rounded-[1.2rem] bg-white/[0.04] px-4 py-3 text-sm text-white/68">
                  {feature}
                </div>
              ))}
            </div>
          </section>
          <section className="rounded-[1.7rem] border border-white/10 bg-white/[0.04] p-5">
            <h3 className="text-sm font-semibold text-white">{t(lang, 'briefGoals')}</h3>
            <div className="mt-4 space-y-3">
              {(briefState.data.goals.length > 0 ? briefState.data.goals : briefState.data.userStories).map((item) => (
                <div key={item} className="rounded-[1.2rem] bg-white/[0.04] px-4 py-3 text-sm text-white/68">
                  {item}
                </div>
              ))}
            </div>
          </section>
        </div>
        {briefState.data.targetUsers?.length > 0 && (
          <section className="mt-5 rounded-[1.7rem] border border-white/10 bg-white/[0.04] p-5">
            <h3 className="text-sm font-semibold text-white">{t(lang, 'briefAudience')}</h3>
            <div className="mt-4 flex flex-wrap gap-3">
              {briefState.data.targetUsers.map((user) => (
                <span key={user} className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 text-sm text-white/66">
                  {user}
                </span>
              ))}
            </div>
          </section>
        )}
      </div>
    ) : (
      <EmptyPanel
        icon={isBuilding ? <RefreshCw size={22} /> : <FileText size={22} />}
        title={isBuilding ? 'Building...' : t(lang, 'noBriefYet')}
        detail={isBuilding ? 'This will be ready when the build completes.' : undefined}
      />
    );
  } else if (activeTab === 'buildPlan') {
    activePanel = planState.loading ? (
      <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'sending')} />
    ) : planState.error ? (
      <EmptyPanel
        icon={<RefreshCw size={22} />}
        title={isBuilding ? 'Building...' : t(lang, 'couldNotLoad')}
        detail={isBuilding ? 'This will be ready when the build completes.' : undefined}
      />
    ) : planState.data ? (
      <ArtifactViewer artifact={planState.data} />
    ) : (
      <EmptyPanel
        icon={isBuilding ? <RefreshCw size={22} /> : <Layers3 size={22} />}
        title={isBuilding ? 'Building...' : t(lang, 'noPlanYet')}
        detail={isBuilding ? 'This will be ready when the build completes.' : undefined}
      />
    );
  } else if (activeTab === 'code') {
    activePanel = <CodePanel lang={lang} projectId={projectId} version={resolvedVersion} isBuilding={isBuilding} />;
  } else if (activeTab === 'changes') {
    activePanel = changesState.loading ? (
      <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'sending')} />
    ) : changesState.error ? (
      <EmptyPanel
        icon={<RefreshCw size={22} />}
        title={isBuilding ? 'Building...' : t(lang, 'couldNotLoad')}
        detail={isBuilding ? 'This will be ready when the build completes.' : undefined}
      />
    ) : changesState.data && changesState.data.length > 0 ? (
      <div className="rounded-[2rem] border border-white/10 bg-[#07101f] p-6 shadow-[0_24px_80px_rgba(2,6,23,0.34)] sm:p-8">
        <h2 className="text-2xl font-semibold tracking-tight text-white">{t(lang, 'whatChangedTitle')}</h2>
        <p className="mt-2 text-sm text-white/46">{t(lang, 'whatChangedSubtitle')}</p>
        <div className="mt-8 space-y-4">
          {changesState.data.map((task) => (
            <div key={task.id} className="rounded-[1.45rem] border border-white/10 bg-white/[0.04] px-5 py-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="text-sm font-semibold text-white">{task.filename}</div>
                <div className="text-xs uppercase tracking-[0.18em] text-white/34">{formatTimestamp(task.timestamp)}</div>
              </div>
              <div className="mt-3 text-sm leading-6 text-white/58">{task.description}</div>
            </div>
          ))}
        </div>
      </div>
    ) : (
      <EmptyPanel
        icon={isBuilding ? <RefreshCw size={22} /> : <History size={22} />}
        title={isBuilding ? 'Building...' : t(lang, 'noChangesYet')}
        detail={isBuilding ? 'This will be ready when the build completes.' : undefined}
      />
    );
  } else if (activeTab === 'insights') {
    activePanel =
      insightsState.insights.length > 0 && insightsState.version != null ? (
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
      ) : (
        <EmptyPanel
          icon={<Lightbulb size={22} />}
          title="No insights yet"
          detail="Build something first to get suggestions."
        />
      );
  } else {
    activePanel = versionsState.loading ? (
      <EmptyPanel icon={<Loader2 size={22} className="animate-spin" />} title={t(lang, 'loadingVersions')} />
    ) : versionsState.error ? (
      <EmptyPanel
        icon={<RefreshCw size={22} />}
        title={isBuilding ? 'Building...' : t(lang, 'couldNotLoad')}
        detail={isBuilding ? 'This will be ready when the build completes.' : undefined}
      />
    ) : versionsState.versions.length === 0 ? (
      <EmptyPanel
        icon={isBuilding ? <RefreshCw size={22} /> : <Clock3 size={22} />}
        title={isBuilding ? 'Building...' : t(lang, 'noVersionsYet')}
        detail={isBuilding ? 'This will be ready when the build completes.' : undefined}
      />
    ) : (
      <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-[#07101f] shadow-[0_24px_80px_rgba(2,6,23,0.34)]">
        <div className="grid min-h-[620px] lg:grid-cols-[330px_minmax(0,1fr)]">
          <aside className="border-b border-white/10 bg-white/[0.03] p-4 lg:border-b-0 lg:border-r">
            <div className="mb-4">
              <div className="text-sm font-semibold text-white">{t(lang, 'versionHistory')}</div>
              <div className="mt-1 text-sm text-white/46">{t(lang, 'savedVersionsHint')}</div>
            </div>
            <div className="custom-scrollbar max-h-[560px] space-y-3 overflow-y-auto pr-1">
              {versionsState.versions.map((item) => {
                const promptPreview =
                  item.prompt_history?.filter((entry) => entry.role === 'user').slice(-1)[0]?.content ||
                  t(lang, 'promptVersionFallback');
                const isActive = versionsState.selectedId === item.id;

                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setVersionsState((current) => ({ ...current, selectedId: item.id }))}
                    className={`block w-full overflow-hidden rounded-[1.4rem] border p-3 text-left transition ${
                      isActive
                        ? 'border-indigo-400/35 bg-indigo-500/10 text-white'
                        : 'border-white/10 bg-white/[0.04] text-white/70 hover:bg-white/[0.08] hover:text-white'
                    }`}
                  >
                    <div className="overflow-hidden rounded-[1rem] border border-white/10 bg-black">
                      <div className="relative h-[120px] overflow-hidden rounded-[1rem]">
                        <iframe
                          title={`Version ${item.version} thumbnail`}
                          src={getPreviewUrl(projectId, item.version)}
                          className="pointer-events-none absolute left-0 top-0 h-[480px] w-[400%] origin-top-left border-0 bg-white"
                          style={{ transform: 'scale(0.25)' }}
                        />
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold">v{item.version}</div>
                      <div className="text-[11px] uppercase tracking-[0.18em] text-white/34">{formatTimestamp(item.created_at)}</div>
                    </div>
                    <div className="mt-2 line-clamp-2 text-sm text-white/52">{promptPreview}</div>
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
                    <div className="text-lg font-semibold text-white">v{selectedVersion.version}</div>
                    <div className="mt-1 text-sm text-white/46">{formatTimestamp(selectedVersion.created_at)}</div>
                  </div>
                  {versionsState.versions.length > 1 && selectedVersion.version !== latestVersion && (
                    <button
                      type="button"
                      onClick={handleRestore}
                      disabled={versionsState.restoringId === selectedVersion.id}
                      className="inline-flex items-center gap-2 rounded-full bg-[linear-gradient(135deg,#4f46e5,#7c3aed,#0891b2)] px-5 py-3 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {versionsState.restoringId === selectedVersion.id ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <RotateCcw size={16} />
                      )}
                      {versionsState.restoringId === selectedVersion.id ? t(lang, 'restoring') : t(lang, 'restoreVersion')}
                    </button>
                  )}
                </div>

                <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.04] p-4">
                  <div className="text-xs uppercase tracking-[0.22em] text-white/36">{t(lang, 'askForChanges')}</div>
                  <div className="mt-3 text-sm leading-6 text-white/64">
                    {selectedVersion.prompt_history?.filter((entry) => entry.role === 'user').slice(-1)[0]?.content ||
                      t(lang, 'promptVersionFallback')}
                  </div>
                </div>

                <div className="flex-1 overflow-hidden rounded-[1.6rem] border border-white/10 bg-black p-3">
                  <div className="h-full overflow-hidden rounded-[1.2rem]">
                    <iframe
                      title={`Version ${selectedVersion.version} preview`}
                      src={getPreviewUrl(projectId, selectedVersion.version)}
                      className="h-[68vh] w-full border-0 bg-white"
                    />
                  </div>
                </div>
              </div>
            ) : (
              <EmptyPanel icon={<Clock3 size={22} />} title={t(lang, 'selectVersion')} />
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex h-full flex-col overflow-hidden bg-[#03050f] text-white">
      <style>{`
        @keyframes detailPulse {
          0% { box-shadow: 0 0 0 0 rgba(129,140,248,0.45); opacity: 0.8; }
          70% { box-shadow: 0 0 0 12px rgba(129,140,248,0); opacity: 0; }
          100% { box-shadow: 0 0 0 0 rgba(129,140,248,0); opacity: 0; }
        }
        @keyframes progressSweep {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(240%); }
        }
        @keyframes nodePulse {
          0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255,255,255,0.14); }
          50% { transform: scale(1.28); box-shadow: 0 0 30px rgba(129,140,248,0.35); }
        }
        @keyframes lineTravel {
          0% { opacity: 0.15; background-position: 0% 50%; }
          50% { opacity: 0.95; background-position: 100% 50%; }
          100% { opacity: 0.15; background-position: 200% 50%; }
        }
        @keyframes panelIn {
          0% { opacity: 0; transform: translateY(8px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .detail-grid {
          background:
            radial-gradient(circle at top, rgba(79,70,229,0.16), transparent 32%),
            radial-gradient(circle at bottom right, rgba(8,145,178,0.14), transparent 26%),
            linear-gradient(180deg, rgba(255,255,255,0.02), transparent 35%);
        }
        .composer-shell:focus-within {
          border-color: rgba(129,140,248,0.42);
          box-shadow: 0 0 0 1px rgba(129,140,248,0.22), 0 0 40px rgba(79,70,229,0.14);
        }
        .build-progress::after {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.46), transparent);
          animation: progressSweep 1.8s linear infinite;
        }
        .neural-node {
          box-shadow: 0 0 24px currentColor;
          animation: nodePulse 2.2s ease-in-out infinite;
        }
        .neural-line {
          background-size: 200% 100%;
          animation: lineTravel 2.4s linear infinite;
        }
        .content-panel-enter {
          animation: panelIn 220ms ease-out;
        }
        button, a {
          -webkit-font-smoothing: antialiased;
          backface-visibility: hidden;
          transform: translateZ(0);
        }
      `}</style>
      <div className="pointer-events-none absolute inset-0 detail-grid" />

      <header className="relative z-50 border-b border-white/10 bg-[#040815]/88 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <button
              type="button"
              onClick={onOpenSidebar}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-white/72 transition hover:bg-white/[0.08] hover:text-white lg:hidden"
              aria-label="Open sidebar"
            >
              <Menu size={18} />
            </button>
            <button
              type="button"
              onClick={onBack}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-white/72 transition hover:bg-white/[0.08] hover:text-white"
              aria-label="Back to home"
            >
              <ArrowLeft size={18} />
            </button>
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-white">{project.name}</div>
              <div className="mt-1 text-xs uppercase tracking-[0.2em] text-white/36">{t(lang, 'savedVersionsHint')}</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs font-medium text-white/72">
              <span className="relative inline-flex h-2.5 w-2.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: tone.color, boxShadow: `0 0 16px ${tone.glow}` }} />
                {project.status === 'RUNNING' && (
                  <span
                    className="absolute inset-0 rounded-full border border-indigo-300/50"
                    style={{ animation: 'detailPulse 1.8s ease-out infinite' }}
                  />
                )}
              </span>
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
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.04] text-white/72 transition hover:bg-white/[0.08] hover:text-white"
              aria-label="Open settings"
            >
              <Settings2 size={18} />
            </button>
          </div>
        </div>
      </header>

      <div className="relative z-10 min-h-0 flex-1 overflow-hidden p-4 sm:p-6">
        <div className="grid h-full min-h-0 gap-5 lg:grid-cols-[260px_48px_minmax(0,1fr)]">
          <aside className="relative min-h-0 rounded-[2rem] border border-white/10 bg-[#07101f] shadow-[0_24px_80px_rgba(2,6,23,0.34)]">
            <div className="absolute inset-0 rounded-[2rem] bg-[radial-gradient(circle_at_top,rgba(79,70,229,0.18),transparent_42%),radial-gradient(circle_at_bottom,rgba(8,145,178,0.12),transparent_36%)]" />
            <div className="relative flex h-full min-h-0 flex-col overflow-hidden rounded-[2rem]">
              <div className="border-b border-white/10 px-5 py-5">
                <div className="flex items-start gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-lg font-semibold text-white">{project.name}</div>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="relative inline-flex h-3 w-3">
                        <span className="h-3 w-3 rounded-full" style={{ backgroundColor: tone.color, boxShadow: `0 0 20px ${tone.glow}` }} />
                        {project.status === 'RUNNING' && (
                          <span
                            className="absolute inset-0 rounded-full border border-indigo-300/50"
                            style={{ animation: 'detailPulse 1.8s ease-out infinite' }}
                          />
                        )}
                      </span>
                      <span className="text-xs uppercase tracking-[0.2em] text-white/44">{getStatusLabel(project, lang)}</span>
                    </div>
                  </div>
                </div>

                {project.status === 'RUNNING' && (
                  <div className="mt-5">
                    <div className="mb-2 flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-white/38">
                      <span>{statusMessage}</span>
                      <span>{progress}%</span>
                    </div>
                    <div className="relative h-2 overflow-hidden rounded-full bg-white/[0.07]">
                      <div className="build-progress relative h-full rounded-full bg-[linear-gradient(90deg,#4f46e5,#7c3aed,#0891b2)]" style={{ width: `${progress}%` }} />
                    </div>
                  </div>
                )}
              </div>

              <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
                <div className="mb-4 text-xs uppercase tracking-[0.24em] text-white/34">{t(lang, 'projectConversation')}</div>
                <div className="space-y-4">
                  <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] p-4">
                    <div className="text-[11px] uppercase tracking-[0.22em] text-white/36">{t(lang, 'originalPrompt')}</div>
                    <div className="mt-3 text-sm leading-6 text-white/66">{project.description}</div>
                  </div>

                  {messages.length > 0 ? (
                    messages.map((message, index) => <ChatBubble key={`${message.role}-${index}-${message.content}`} message={message} />)
                  ) : (
                    <div className="rounded-[1.4rem] border border-dashed border-white/10 p-4 text-sm text-white/44">
                      {t(lang, 'emptyConversation')}
                    </div>
                  )}

                  {project.status === 'COMPLETED' && (
                    <div className="rounded-[1.4rem] border border-emerald-400/20 bg-emerald-500/10 p-4 text-sm text-emerald-100">
                      {t(lang, 'buildReady')}
                    </div>
                  )}
                  {project.status === 'FAILED' && (
                    <div className="rounded-[1.4rem] border border-rose-400/20 bg-rose-500/10 p-4 text-sm text-rose-100">
                      {t(lang, 'buildFailed')}
                    </div>
                  )}
                  <div ref={endRef} />
                </div>
              </div>

              <div className="border-t border-white/10 px-5 py-4">
                {composerError && (
                  <div className="mb-3 rounded-[1.2rem] border border-amber-400/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                    {composerError}
                  </div>
                )}
                <form onSubmit={handleSendMessage}>
                  <div className="composer-shell rounded-[1.5rem] border border-white/10 bg-white/[0.04] p-3 transition">
                    <textarea
                      ref={chatTextareaRef}
                      value={chatInput}
                      onChange={(event) => {
                        setChatInput(event.target.value);
                        if (composerError) setComposerError(null);
                      }}
                      onKeyDown={(event) => {
                        if (event.key !== 'Enter' || event.shiftKey) return;
                        event.preventDefault();
                        event.currentTarget.form?.requestSubmit();
                      }}
                      disabled={chatLoading || project.status === 'RUNNING'}
                      placeholder={project.status === 'RUNNING' ? t(lang, 'buildInProgress') : t(lang, 'chatComposerPlaceholder')}
                      className="min-h-[92px] w-full resize-none border-0 bg-transparent px-1 py-1 text-sm leading-6 text-white outline-none placeholder:text-white/28"
                    />
                    <button
                      type="submit"
                      disabled={!chatInput.trim() || chatLoading || project.status === 'RUNNING'}
                      className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[linear-gradient(135deg,#4f46e5,#7c3aed,#0891b2)] px-4 py-3 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(79,70,229,0.28)] transition hover:scale-[1.005] disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {chatLoading ? <Loader2 size={16} className="animate-spin" /> : <SendHorizontal size={16} />}
                      {chatLoading ? t(lang, 'thinking') : t(lang, 'askForChanges')}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </aside>

          <div className="hidden lg:flex flex-col items-center justify-center gap-2 py-8">
            <div className="flex flex-col gap-2 rounded-full border border-white/10 bg-[#060b19]/92 p-2 backdrop-blur-xl">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  title={tab.label}
                  onClick={() => handleTabChange(tab.id)}
                  className={`group relative flex h-10 w-10 items-center justify-center rounded-full transition ${
                    activeTab === tab.id
                      ? 'bg-[linear-gradient(135deg,#4f46e5,#7c3aed)] text-white shadow-[0_12px_30px_rgba(79,70,229,0.35)]'
                      : 'bg-white/[0.04] text-white/56 hover:bg-white/[0.08] hover:text-white'
                  }`}
                >
                  <tab.icon size={16} />
                  {tab.id === 'insights' && insightsUnread && (
                    <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-amber-400 shadow-[0_0_6px_rgba(251,191,36,0.8)]" />
                  )}
                  <span className="pointer-events-none absolute right-[calc(100%+10px)] whitespace-nowrap rounded-full border border-white/10 bg-[#09101f] px-3 py-1.5 text-xs font-medium text-white/80 opacity-0 transition group-hover:opacity-100">
                    {tab.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          <section ref={rightPanelRef} className="custom-scrollbar min-h-0 overflow-y-auto pr-1">
            <div key={`${activeTab}-${resolvedVersion ?? 'none'}-${project.status}`} className="content-panel-enter space-y-4">
              {activePanel}
            </div>
          </section>
        </div>
      </div>

      {showRegisterPrompt && !hasSession && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/50 p-4 backdrop-blur-sm sm:items-center">
          <div className="w-full max-w-lg rounded-[2rem] border border-white/10 bg-[#09101f] p-6 text-white shadow-[0_30px_80px_rgba(2,6,23,0.55)] sm:p-7">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium uppercase tracking-[0.18em] text-emerald-200">
              <Sparkles size={14} />
              Build Ready
            </div>
            <h3 className="mt-4 text-2xl font-semibold tracking-tight text-white">
              Your app is ready! Create a free account to save it and keep building.
            </h3>
            <p className="mt-3 text-sm leading-6 text-white/58">
              You can keep reviewing this version right now. Create an account whenever you want to save this project and keep iterating from it.
            </p>
            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={() => onNavigate(`/register?guest_project_id=${encodeURIComponent(projectId)}`)}
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-[1.25rem] bg-[linear-gradient(135deg,#4f46e5,#7c3aed,#0891b2)] px-4 py-3 text-sm font-semibold text-white transition hover:brightness-110"
              >
                Create Account
                <ExternalLink size={16} />
              </button>
              <button
                type="button"
                onClick={() => setShowRegisterPrompt(false)}
                className="inline-flex flex-1 items-center justify-center rounded-[1.25rem] border border-white/10 px-4 py-3 text-sm font-medium text-white/68 transition hover:bg-white/[0.05] hover:text-white"
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
