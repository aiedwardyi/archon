import { v4 as uuidv4 } from 'uuid';
import { AgentStage, Artifact, EngineerTask, Project } from '../types';

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5000';
const API_ROOT = `${API_BASE.replace(/\/$/, '')}/api`;

export interface PromptHistoryEntry {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface BriefRecord {
  title: string;
  summary: string;
  goals: string[];
  features: string[];
  userStories: string[];
  targetUsers: string[];
  techStackRecommendation: string[];
}

export interface VersionRecord {
  id: string;
  version: number;
  status: string;
  created_at: string;
  prompt_history?: PromptHistoryEntry[];
}

export interface VersionTreeNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: VersionTreeNode[];
}

export class HttpError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown, message?: string) {
    super(message || `HTTP ${status}`);
    this.name = 'HttpError';
    this.status = status;
    this.body = body;
  }
}

function normalizeStatus(status: unknown): Project['status'] {
  const value = String(status || '').toUpperCase();
  if (value === 'COMPLETED' || value === 'SUCCESS') return 'COMPLETED';
  if (value === 'FAILED' || value === 'ERROR') return 'FAILED';
  if (value === 'RUNNING' || value === 'IN_PROGRESS' || value === 'PENDING') return 'RUNNING';
  return 'IDLE';
}

function normalizeStage(stage: unknown): AgentStage {
  const value = String(stage || '').toLowerCase();
  if (value === 'pm' || value === 'planner' || value === 'engineer' || value === 'complete') {
    return value;
  }
  return 'idle';
}

function toHeaderObject(headers?: HeadersInit): Record<string, string> {
  if (!headers) return {};
  if (headers instanceof Headers) return Object.fromEntries(headers.entries());
  if (Array.isArray(headers)) return Object.fromEntries(headers);
  return headers as Record<string, string>;
}

export function buildApiUrl(path: string): string {
  return `${API_ROOT}${path.startsWith('/') ? path : `/${path}`}`;
}

export function getPreviewUrl(projectId: string, version: number): string {
  return buildApiUrl(`/preview/${projectId}/${version}`);
}

export function getAuthHeaders(headers?: HeadersInit): Record<string, string> {
  const token = localStorage.getItem('archon_token');
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...toHeaderObject(headers),
  };
}

export function isNetworkError(error: unknown): boolean {
  return !(error instanceof HttpError);
}

export function isAuthError(error: unknown): boolean {
  return error instanceof HttpError && (error.status === 401 || error.status === 403 || error.status === 422);
}

async function parseErrorBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || '';
  try {
    if (contentType.includes('application/json')) {
      return await response.json();
    }
    return await response.text();
  } catch {
    return null;
  }
}

export async function apiRequest(path: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: getAuthHeaders(init.headers),
  });

  if (!response.ok) {
    throw new HttpError(response.status, await parseErrorBody(response));
  }

  return response;
}

export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await apiRequest(path, init);
  return response.json() as Promise<T>;
}

export function normalizePrd(raw: any): BriefRecord {
  const prd = raw?.prd || raw;
  return {
    title: prd?.document_title || prd?.title || 'Brief',
    summary: prd?.overview || prd?.summary || '',
    goals: prd?.goals || prd?.requirements || [],
    features: prd?.core_features_mvp || prd?.features || prd?.goals || [],
    userStories: prd?.user_stories || prd?.userStories || [],
    targetUsers: prd?.target_users || prd?.targetUsers || [],
    techStackRecommendation: prd?.technical_stack_recommendation || prd?.techStackRecommendation || [],
  };
}

export function normalizePlan(raw: any) {
  const milestones = raw?.milestones || raw?.plan?.milestones || raw?.phases || [];
  return {
    phases: milestones.map((milestone: any) => ({
      name: milestone.name || 'Milestone',
      description: (milestone.tasks || []).map((task: any) => task.description).join(' · ') || '',
      steps: (milestone.tasks || []).map((task: any) => task.description || task.id || 'Task'),
    })),
    estimatedTimeline: `${milestones.length} milestone${milestones.length === 1 ? '' : 's'}`,
  };
}

function normalizeCode(raw: any) {
  const outputs = raw?.outputs || {};
  const writes = outputs.writes || [];
  const summary = outputs.summary || 'Build complete.';
  const files = writes.map((write: any) => {
    const fullPath = String(write.path || '');
    const filename = fullPath.split('\\').pop() || fullPath.split('/').pop() || 'file';
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    const languageMap: Record<string, string> = {
      py: 'python',
      js: 'javascript',
      ts: 'typescript',
      tsx: 'tsx',
      jsx: 'jsx',
      md: 'markdown',
      txt: 'plaintext',
      json: 'json',
      yml: 'yaml',
      yaml: 'yaml',
      html: 'html',
      css: 'css',
      sh: 'bash',
      gitignore: 'plaintext',
    };

    return {
      filename,
      language: languageMap[ext] || 'plaintext',
      content: `// ${filename}\n// Generated file\n// Size: ${write.bytes} bytes\n// SHA256: ${write.sha256}\n\n// Full path: ${fullPath}`,
    };
  });

  return {
    files: [
      {
        filename: '_summary.md',
        language: 'markdown',
        content: `# Build Summary\n\n${summary}\n\n## Files (${writes.length})\n\n${writes
          .map((write: any) => `- ${write.path.split('\\').pop() || write.path} (${write.bytes} bytes)`)
          .join('\n')}`,
      },
      ...files,
    ],
  };
}

function normalizeProject(raw: any): Project {
  return {
    ...raw,
    id: String(raw.id),
    createdAt: raw.createdAt ?? (raw.created_at ? new Date(raw.created_at).getTime() : Date.now()),
    status: normalizeStatus(raw.status),
    currentStage: normalizeStage(raw.currentStage),
    engineerTasks: raw.engineerTasks || [],
  };
}

export function buildTasksFromResult(raw: any): EngineerTask[] {
  const outputs = raw?.outputs || {};
  const writes = outputs.writes || [];
  const producedAt = raw?._meta?.produced_at ? new Date(raw._meta.produced_at).getTime() : Date.now();

  if (writes.length > 0) {
    return writes.map((write: any, index: number) => {
      const fullPath = String(write.path || '');
      const filename = fullPath.split('\\').pop() || fullPath.split('/').pop() || `file-${index}`;
      return {
        id: uuidv4(),
        filename,
        timestamp: producedAt + index * 100,
        description: `Generated ${filename} (${write.bytes} bytes)`,
      };
    });
  }

  const summary = String(outputs.summary || '').trim();
  const filesGenerated = Number(outputs.files_generated || 0);

  if (!summary && !filesGenerated) {
    return [];
  }

  return [
    {
      id: uuidv4(),
      filename: filesGenerated > 0 ? `${filesGenerated} file${filesGenerated === 1 ? '' : 's'} updated` : 'Build summary',
      timestamp: producedAt,
      description: summary || `Updated ${filesGenerated} generated file${filesGenerated === 1 ? '' : 's'}.`,
    },
  ];
}

export async function fetchProjectHead(projectId: string) {
  return apiJson<{ project_id: number; version: number; execution_id: number }>(`/projects/${projectId}/head`);
}

export async function fetchVersions(projectId: string): Promise<VersionRecord[]> {
  const data = await apiJson<{ versions?: VersionRecord[] } | VersionRecord[]>(`/projects/${projectId}/versions`);
  return Array.isArray(data) ? data : data.versions || [];
}

export async function restoreVersion(executionId: string) {
  return apiJson<{ message: string }>(`/executions/${executionId}/restore`, { method: 'POST' });
}

export async function fetchBrief(projectId: string, version: number) {
  const data = await apiJson(`/prd?project_id=${projectId}&version=${version}`);
  return normalizePrd(data);
}

export async function fetchPlan(projectId: string, version: number) {
  const data = await apiJson(`/plan?project_id=${projectId}&version=${version}`);
  return normalizePlan(data);
}

export async function fetchCodeArtifact(projectId: string, version: number) {
  const data = await apiJson(`/code?project_id=${projectId}&version=${version}`);
  return {
    artifact: normalizeCode(data),
    tasks: buildTasksFromResult(data),
  };
}

export async function fetchChatHistory(projectId: string): Promise<PromptHistoryEntry[]> {
  return apiJson(`/projects/${projectId}/chat-history`);
}

export async function saveChatMessages(projectId: string, messages: PromptHistoryEntry[]) {
  return apiJson(`/projects/${projectId}/chat-messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  });
}

export async function classifyProjectMessage(projectId: string, message: string) {
  return apiJson<{ response_type: 'chat' | 'build'; message?: string }>(`/projects/${projectId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  });
}

export async function iterateProject(projectId: string, prompt: string, promptHistory: PromptHistoryEntry[]) {
  return apiJson<{ status: string; project_id: number; execution_id: number; version: number }>(`/projects/${projectId}/iterate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, prompt_history: promptHistory }),
  });
}

export async function fetchVersionTree(projectId: string, version: number) {
  return apiJson<{ tree: VersionTreeNode[] }>(`/projects/${projectId}/versions/${version}/files`);
}

export async function fetchVersionFile(projectId: string, version: number, path: string) {
  return apiJson<{ path: string; content: string; language: string }>(
    `/projects/${projectId}/versions/${version}/files?path=${encodeURIComponent(path)}`
  );
}

class BackendService {
  private projects: Project[] = [];
  private artifacts: Artifact[] = [];
  private listeners: Array<() => void> = [];
  private pollingIntervals = new Map<string, ReturnType<typeof setInterval>>();
  private isConnected = true;
  private hasNetworkError = false;
  private artifactExecutionIds = new Map<string, string>();

  constructor() {
    if (typeof window !== 'undefined' && localStorage.getItem('archon_token')) {
      void this.silentFetchProjects();
    }
  }

  subscribe(callback: () => void) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((listener) => listener !== callback);
    };
  }

  private notify() {
    this.listeners.forEach((listener) => listener());
  }

  private setReachability(isReachable: boolean) {
    this.isConnected = isReachable;
    this.hasNetworkError = !isReachable;
  }

  private async silentFetchProjects() {
    try {
      const projects = await apiJson<any[]>('/projects');
      this.projects = projects.map(normalizeProject);
      this.projects.forEach((project) => {
        if (project.status !== 'RUNNING') {
          sessionStorage.removeItem(`progress-${project.id}`);
        }
      });
      this.setReachability(true);
    } catch (error) {
      if (isNetworkError(error)) {
        this.setReachability(false);
      } else {
        this.setReachability(true);
      }
    } finally {
      this.notify();
    }
  }

  async fetchProjects() {
    try {
      const projects = await apiJson<any[]>('/projects');
      this.projects = projects.map(normalizeProject);
      this.projects.forEach((project) => {
        if (project.status !== 'RUNNING') {
          sessionStorage.removeItem(`progress-${project.id}`);
        }
      });
      this.setReachability(true);
    } catch (error) {
      if (isNetworkError(error)) {
        this.setReachability(false);
      } else {
        this.setReachability(true);
      }
      throw error;
    } finally {
      this.notify();
    }
  }

  getIsConnected() {
    return this.isConnected;
  }

  getHasNetworkError() {
    return this.hasNetworkError;
  }

  async retryConnection() {
    try {
      await this.fetchProjects();
    } catch {
      // The UI only needs the updated reachability state.
    }
  }

  getProjects() {
    return [...this.projects].sort((left, right) => right.createdAt - left.createdAt);
  }

  getProject(id: string) {
    return this.projects.find((project) => project.id === id);
  }

  clearProjects() {
    this.projects = [];
    this.artifacts = [];
    this.artifactExecutionIds.clear();
    this.pollingIntervals.forEach((interval) => clearInterval(interval));
    this.pollingIntervals.clear();
    this.notify();
  }

  getArtifacts(projectId: string) {
    return this.artifacts
      .filter((artifact) => artifact.projectId === projectId)
      .sort((left, right) => left.createdAt - right.createdAt);
  }

  async createProject(name: string, description: string) {
    try {
      const created = normalizeProject(
        await apiJson('/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, description }),
        })
      );
      this.projects.push(created);
      this.setReachability(true);
      this.notify();
      return created;
    } catch (error) {
      if (isNetworkError(error)) {
        this.setReachability(false);
      } else {
        this.setReachability(true);
      }
      this.notify();
      throw error;
    }
  }

  async deleteProject(id: string) {
    try {
      await apiRequest(`/projects/${id}`, { method: 'DELETE' });
      this.projects = this.projects.filter((project) => project.id !== id);
      this.artifacts = this.artifacts.filter((artifact) => artifact.projectId !== id);
      this.artifactExecutionIds.delete(id);
      const interval = this.pollingIntervals.get(id);
      if (interval) {
        clearInterval(interval);
        this.pollingIntervals.delete(id);
      }
      this.setReachability(true);
      this.notify();
      return true;
    } catch (error) {
      if (isNetworkError(error)) {
        this.setReachability(false);
      } else {
        this.setReachability(true);
      }
      this.notify();
      throw error;
    }
  }

  async startExecution(projectId: string) {
    const project = this.getProject(projectId);
    if (!project) return;

    this.artifacts = this.artifacts.filter((artifact) => artifact.projectId !== projectId);
    this.artifactExecutionIds.delete(projectId);
    project.status = 'RUNNING';
    project.currentStage = 'pm';
    project.engineerTasks = [];
    this.notify();

    try {
      await apiJson('/execute-task', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: Number(projectId) }),
      });
      this.setReachability(true);
      this.startPolling(projectId);
    } catch (error) {
      project.status = 'FAILED';
      if (isNetworkError(error)) {
        this.setReachability(false);
      } else {
        this.setReachability(true);
      }
      this.notify();
      throw error;
    }
  }

  async startIteration(projectId: string, prompt: string, promptHistory: PromptHistoryEntry[]) {
    const project = this.getProject(projectId);
    if (!project) return;

    this.artifacts = this.artifacts.filter((artifact) => artifact.projectId !== projectId);
    this.artifactExecutionIds.delete(projectId);
    project.status = 'RUNNING';
    project.currentStage = 'pm';
    project.engineerTasks = [];
    this.notify();

    try {
      await iterateProject(projectId, prompt, promptHistory);
      this.setReachability(true);
      this.startPolling(projectId);
    } catch (error) {
      project.status = 'FAILED';
      if (isNetworkError(error)) {
        this.setReachability(false);
      } else {
        this.setReachability(true);
      }
      this.notify();
      throw error;
    }
  }

  private startPolling(projectId: string) {
    const existing = this.pollingIntervals.get(projectId);
    if (existing) {
      clearInterval(existing);
    }

    const interval = setInterval(async () => {
      try {
        const data = await apiJson<any>(`/execution-status?project_id=${projectId}`);
        const project = this.getProject(projectId);
        if (!project) {
          clearInterval(interval);
          this.pollingIntervals.delete(projectId);
          return;
        }

        project.status = normalizeStatus(data.status);
        project.currentStage = normalizeStage(data.currentStage);
        project.engineerTasks = data.engineerTasks || [];
        this.setReachability(true);

        await this.syncArtifacts(projectId, project.currentStage, project.status, data.execution_id);
        this.notify();

        if (project.status === 'COMPLETED' || project.status === 'FAILED') {
          clearInterval(interval);
          this.pollingIntervals.delete(projectId);
        }
      } catch (error) {
        if (isNetworkError(error)) {
          this.setReachability(false);
        } else {
          this.setReachability(true);
        }
        this.notify();
      }
    }, 2000);

    this.pollingIntervals.set(projectId, interval);
  }

  private async syncArtifacts(projectId: string, stage: AgentStage, status: Project['status'], executionId?: string) {
    const cacheKey = executionId ? `${projectId}-${executionId}` : projectId;
    const previousCacheKey = this.artifactExecutionIds.get(projectId);

    if (executionId && previousCacheKey !== cacheKey) {
      this.artifacts = this.artifacts.filter((artifact) => artifact.projectId !== projectId);
      this.artifactExecutionIds.set(projectId, cacheKey);
    }

    const fetchArtifact = async (
      type: Artifact['type'],
      path: string,
      title: string,
      normalize: (raw: any) => any
    ) => {
      const exists = this.artifacts.some((artifact) => artifact.projectId === projectId && artifact.type === type);
      if (exists) return;

      try {
        const content = normalize(await apiJson(`${path}?project_id=${projectId}`));
        this.artifacts.push({
          id: uuidv4(),
          projectId,
          type,
          title,
          content,
          createdAt: Date.now(),
          agent: 'Archon',
        });
      } catch (error) {
        if (error instanceof HttpError && error.status === 404) {
          return;
        }
        if (isNetworkError(error)) {
          this.setReachability(false);
        }
      }
    };

    if (stage === 'planner' || stage === 'engineer' || stage === 'complete' || status === 'COMPLETED') {
      await fetchArtifact('PRD', '/prd', 'Brief', normalizePrd);
    }

    if (stage === 'engineer' || stage === 'complete' || status === 'COMPLETED') {
      await fetchArtifact('PLAN', '/plan', 'Build Plan', normalizePlan);
    }

    if (status === 'COMPLETED') {
      await fetchArtifact('CODE', '/code', 'Code', normalizeCode);
      if (!this.getProject(projectId)?.engineerTasks?.length) {
        try {
          const raw = await apiJson(`/code?project_id=${projectId}`);
          const project = this.getProject(projectId);
          if (project) {
            project.engineerTasks = buildTasksFromResult(raw);
          }
        } catch {
          // Ignore non-critical task generation failures.
        }
      }
    }
  }
}

export const backend = new BackendService();
