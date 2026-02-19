import { useState, useEffect, useRef } from 'react';
import { Check, Loader2, Clock, ArrowRight, Send } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { getExecutionStatus, iterateProject, getProject, type ExecutionStatus, type Project, type Execution } from '@/services/api';

const AGENTS = [
  { id: 'pm', name: 'Requirements Agent', description: 'Understands your request' },
  { id: 'planner', name: 'Architecture Agent', description: 'Plans the build' },
  { id: 'engineer', name: 'Build Agent', description: 'Writes your code' },
];

const STAGE_ORDER = ['pm', 'planner', 'engineer'];

function agentStatus(agentId: string, currentStage: string, overallStatus: string) {
  if (overallStatus === 'COMPLETED') return 'complete';
  if (overallStatus === 'FAILED') {
    const agentIdx = STAGE_ORDER.indexOf(agentId);
    const stageIdx = STAGE_ORDER.indexOf(currentStage);
    return agentIdx < stageIdx ? 'complete' : agentIdx === stageIdx ? 'running' : 'pending';
  }
  const agentIdx = STAGE_ORDER.indexOf(agentId);
  const stageIdx = STAGE_ORDER.indexOf(currentStage);
  if (agentIdx < stageIdx) return 'complete';
  if (agentIdx === stageIdx) return 'running';
  return 'pending';
}

// ─── sessionStorage helpers ────────────────────────────────────────────────────

function cacheProject(id: number, name: string) {
  sessionStorage.setItem(`project_name_${id}`, name);
}
function getCachedName(id: number | null): string | null {
  if (!id) return null;
  return sessionStorage.getItem(`project_name_${id}`);
}

function cacheExecutionLogs(execId: number, logs: { id: string; timestamp: number; message: string; type: string }[]) {
  try {
    sessionStorage.setItem(`logs_exec_${execId}`, JSON.stringify(logs));
  } catch (e) { /* storage full */ }
}
function getCachedLogs(execId: number | null): { id: string; timestamp: number; message: string; type: string }[] | null {
  if (!execId) return null;
  const raw = sessionStorage.getItem(`logs_exec_${execId}`);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

interface CachedRunState { displayStatus: 'COMPLETED' | 'FAILED'; currentStage: string; }
function cacheRunState(projectId: number, state: CachedRunState) {
  sessionStorage.setItem(`run_state_${projectId}`, JSON.stringify(state));
}
function getCachedRunState(projectId: number | null): CachedRunState | null {
  if (!projectId) return null;
  const raw = sessionStorage.getItem(`run_state_${projectId}`);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function buildRestoredLogs(execution: Execution) {
  const history: { id: string; timestamp: number; message: string; type: string }[] = [];
  const t = new Date(execution.created_at).getTime();
  const add = (msg: string, offset = 0) =>
    history.push({ id: `r-${offset}`, timestamp: t + offset, message: msg, type: 'info' });
  add('Starting pipeline...', 0);
  add('Requirements Agent: Analyzing your request...', 500);
  add('Requirements Agent: Brief created.', 1000);
  add('Architecture Agent: Planning the build...', 1500);
  add('Architecture Agent: Build plan ready.', 2000);
  add('Build Agent: Writing your code...', 2500);
  if (execution.status === 'success') add('Build complete.', 3000);
  else if (execution.status === 'error') add(`Something went wrong: ${execution.error_message || 'Unknown error'}`, 3000);
  return history;
}

export default function PipelineRun() {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project') ? Number(searchParams.get('project')) : null;

  const cachedRunState = getCachedRunState(projectId);
  const [project, setProject] = useState<Project | null>(null);
  const [projectName, setProjectName] = useState<string | null>(() => getCachedName(projectId));

  // Single source of truth for what to display in the log panel
  // 'idle' = no run yet, 'sending' = waiting for backend to accept, 'running' = live polling, 'done' = completed
  type RunPhase = 'idle' | 'sending' | 'running' | 'done';
  const [runPhase, setRunPhase] = useState<RunPhase>(() => cachedRunState ? 'done' : 'idle');
  const [liveStatus, setLiveStatus] = useState<ExecutionStatus | null>(null);
  const [displayedLogs, setDisplayedLogs] = useState<{ id: string; timestamp: number; message: string; type: string }[]>([]);
  const [displayedStatus, setDisplayedStatus] = useState<'COMPLETED' | 'FAILED' | null>(
    () => cachedRunState?.displayStatus ?? null
  );
  const [currentStage, setCurrentStage] = useState<string>(
    () => cachedRunState?.currentStage ?? 'engineer'
  );

  const [input, setInput] = useState('');
  const [promptHistory, setPromptHistory] = useState<{ role: string; content: string }[]>([]);
  const [sending, setSending] = useState(false);
  const [startedAt, setStartedAt] = useState<Date | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const seenRunningRef = useRef(false);
  const activeHeadExecIdRef = useRef<number | null>(null);

  // Reset on project switch — seed from cache instantly
  useEffect(() => {
    const cached = getCachedRunState(projectId);
    setProject(null);
    setProjectName(getCachedName(projectId));
    setLiveStatus(null);
    setRunPhase(cached ? 'done' : 'idle');
    setDisplayedStatus(cached?.displayStatus ?? null);
    setCurrentStage(cached?.currentStage ?? 'engineer');
    setDisplayedLogs([]);
    setStartedAt(null);
    setElapsed(0);
    setPromptHistory([]);
    seenRunningRef.current = false;
    activeHeadExecIdRef.current = null;
  }, [projectId]);

  // Load project + restore logs from sessionStorage or fallback
  useEffect(() => {
    if (!projectId) return;
    getProject(projectId)
      .then((p) => {
        setProject(p);
        setProjectName(p.name);
        cacheProject(p.id, p.name);
        const head = p.executions?.find((e: Execution) => e.is_active_head);
        if (head?.prompt_history?.length) setPromptHistory(head.prompt_history);
        if (head && (head.status === 'success' || head.status === 'error')) {
          activeHeadExecIdRef.current = head.id;
          const logsToShow = getCachedLogs(head.id) ?? buildRestoredLogs(head);
          const finalStatus = head.status === 'success' ? 'COMPLETED' : 'FAILED';
          setDisplayedLogs(logsToShow);
          setDisplayedStatus(finalStatus);
          setCurrentStage('engineer');
          setRunPhase('done');
          cacheRunState(p.id, { displayStatus: finalStatus, currentStage: 'engineer' });
        }
      })
      .catch(console.error);
  }, [projectId]);

  // Initial poll — detect if a run is already happening for this project
  useEffect(() => {
    if (!projectId) return;
    function poll() {
      getExecutionStatus()
        .then((s) => {
          const belongsHere = s.status === 'RUNNING' && s.project_id === projectId;
          if (belongsHere) {
            seenRunningRef.current = true;
            setRunPhase('running');
            setLiveStatus(s);
            setCurrentStage(s.currentStage || 'pm');
            setDisplayedStatus(null);
          } else if (seenRunningRef.current) {
            // Transition: running → done
            const execId = activeHeadExecIdRef.current ?? s.execution_id ?? null;
            if (execId) cacheExecutionLogs(execId, s.logs);
            const finalStatus = s.status as 'COMPLETED' | 'FAILED';
            if (projectId) cacheRunState(projectId, { displayStatus: finalStatus, currentStage: s.currentStage || 'engineer' });
            setDisplayedLogs(s.logs || []);
            setDisplayedStatus(finalStatus);
            setCurrentStage(s.currentStage || 'engineer');
            setRunPhase('done');
            setLiveStatus(null);
            seenRunningRef.current = false;
          }
          if (s.status !== 'RUNNING') {
            clearInterval(pollingRef.current!);
            pollingRef.current = null;
          }
        })
        .catch(console.error);
    }
    poll();
    pollingRef.current = setInterval(poll, 2000);
    return () => clearInterval(pollingRef.current!);
  }, [projectId]);

  // Elapsed timer while running
  useEffect(() => {
    if (runPhase !== 'running') return;
    if (!startedAt) setStartedAt(new Date());
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, [runPhase]);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [liveStatus?.logs, displayedLogs]);

  async function handleSend() {
    if (!input.trim() || !projectId || sending) return;
    const prompt = input.trim();
    setInput('');
    setSending(true);
    setStartedAt(null);
    setElapsed(0);
    // Clear logs immediately and show "sending" phase — no blank placeholder
    setRunPhase('sending');
    setLiveStatus(null);
    setDisplayedLogs([]);
    setDisplayedStatus(null);
    seenRunningRef.current = false;

    const newHistory = [...promptHistory, { role: 'user', content: prompt }];
    setPromptHistory(newHistory);

    try {
      const { execution_id } = await iterateProject(projectId, prompt, newHistory);
      activeHeadExecIdRef.current = execution_id;

      // Switch to running phase — poll for live status
      setRunPhase('running');
      clearInterval(pollingRef.current!);
      pollingRef.current = setInterval(async () => {
        const s = await getExecutionStatus();
        const belongsHere = s.status === 'RUNNING' && s.project_id === projectId;
        if (belongsHere) {
          seenRunningRef.current = true;
          setLiveStatus(s);
          setCurrentStage(s.currentStage || 'pm');
        } else if (seenRunningRef.current) {
          // Save logs and transition to done
          const execId = activeHeadExecIdRef.current ?? s.execution_id ?? null;
          if (execId) cacheExecutionLogs(execId, s.logs);
          const finalStatus = s.status as 'COMPLETED' | 'FAILED';
          if (projectId) cacheRunState(projectId, { displayStatus: finalStatus, currentStage: 'engineer' });
          setDisplayedLogs(s.logs || []);
          setDisplayedStatus(finalStatus);
          setCurrentStage('engineer');
          setRunPhase('done');
          setLiveStatus(null);
          seenRunningRef.current = false;
          clearInterval(pollingRef.current!);
          pollingRef.current = null;
        }
      }, 2000);
    } catch (e) {
      console.error(e);
      setRunPhase('idle');
    } finally {
      setSending(false);
    }
  }

  const isRunning = runPhase === 'running';
  const isSending = runPhase === 'sending';

  // What to show in the log panel
  const logs = isRunning ? (liveStatus?.logs || []) : displayedLogs;

  // Agent card overall status
  const overallStatus = isRunning ? 'RUNNING' : displayedStatus ?? '';

  const versionLabel = isRunning || isSending ? '...' : (project?.execution_count ?? '—');
  const displayName = projectName ?? (projectId ? '...' : 'No project selected');
  const displaySub = projectId
    ? `Version ${versionLabel}${startedAt && isRunning ? ` · Started ${elapsed}s ago` : ''}`
    : 'Select a project from Projects page';

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="flex-1 overflow-auto px-5 py-5">
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-0.5">
            <h1 className="text-base font-semibold text-foreground">{displayName}</h1>
            {(isRunning || isSending) && (
              <span className="rounded bg-secondary px-2 py-0.5 text-[10px] font-medium text-status-running">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-status-running mr-1 align-middle status-pulse" />
                Building...
              </span>
            )}
            {displayedStatus === 'COMPLETED' && !isRunning && !isSending && (
              <span className="rounded bg-secondary px-2 py-0.5 text-[10px] font-medium text-status-complete">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-status-complete mr-1 align-middle" />
                Done
              </span>
            )}
            {displayedStatus === 'FAILED' && !isRunning && !isSending && (
              <span className="rounded bg-secondary px-2 py-0.5 text-[10px] font-medium text-status-failed">
                Failed
              </span>
            )}
          </div>
          <p className="text-[11px] text-muted-foreground">{displaySub}</p>
        </div>

        <div className="flex items-stretch gap-0 mb-6">
          {AGENTS.map((agent, i) => {
            const agSt = agentStatus(agent.id, currentStage, overallStatus);
            return (
              <div key={agent.id} className="flex items-center">
                <div className={`rounded border p-3 min-w-[200px] transition-all ${
                  agSt === 'running'
                    ? 'border-status-running/40 bg-status-running/5'
                    : agSt === 'complete'
                    ? 'border-border bg-card'
                    : 'border-border bg-secondary/30'
                }`}>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    {agSt === 'complete' && <Check className="h-3.5 w-3.5 text-status-complete" />}
                    {agSt === 'running' && <Loader2 className="h-3.5 w-3.5 text-status-running animate-spin" />}
                    {agSt === 'pending' && <Clock className="h-3.5 w-3.5 text-muted-foreground" />}
                    <span className="text-xs font-medium text-foreground">{agent.name}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground mb-1.5">{agent.description}</p>
                  <span className={`rounded bg-secondary px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider ${
                    agSt === 'running' ? 'text-status-running' : 'text-muted-foreground'
                  }`}>
                    {agSt === 'complete' ? 'Done' : agSt === 'running' ? 'Building...' : '—'}
                  </span>
                </div>
                {i < AGENTS.length - 1 && (
                  <ArrowRight className="h-3.5 w-3.5 text-muted-foreground mx-2 flex-shrink-0" />
                )}
              </div>
            );
          })}
        </div>

        <div className="rounded border border-border bg-card">
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="text-[11px] font-medium text-foreground uppercase tracking-wider">Live Output</span>
            <span className="text-[11px] text-muted-foreground font-mono">{logs.length} entries</span>
          </div>
          <div className="p-3 font-mono text-[11px] space-y-0.5 max-h-[320px] overflow-auto">
            {/* Sending phase: waiting for backend to accept the prompt */}
            {isSending && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Starting pipeline...</span>
              </div>
            )}
            {/* Idle: no run yet */}
            {!isSending && logs.length === 0 && (
              <div className="text-muted-foreground italic">
                {projectId ? 'Type a prompt below to start building.' : 'Select a project to get started.'}
              </div>
            )}
            {logs.map((log, i) => (
              <div key={log.id || i} className="flex gap-2 leading-relaxed">
                <span className="text-muted-foreground/50 select-none w-20 flex-shrink-0 text-[10px]">
                  {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
                <span className={log.message.startsWith('Something went wrong') ? 'text-status-failed' : 'text-foreground/80'}>
                  {log.message}
                </span>
              </div>
            ))}
            {isRunning && (
              <div className="flex items-center gap-2 text-muted-foreground pt-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span>Waiting for output...</span>
              </div>
            )}
            <div ref={logsEndRef} />
          </div>
        </div>

        {promptHistory.length > 0 && (
          <div className="mt-4 space-y-1">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1.5">Conversation</p>
            {promptHistory.map((turn, i) => (
              <div key={i} className="flex gap-2 text-[11px]">
                <span className="text-muted-foreground font-mono w-10 flex-shrink-0">{turn.role}</span>
                <span className="text-foreground/80">{turn.content}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-border bg-card px-5 py-2.5">
        <div className="relative max-w-3xl">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={projectId ? 'What would you like to change?' : 'Select a project first'}
            disabled={isRunning || isSending}
            className="w-full rounded border border-border bg-background pl-3 pr-10 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isRunning || isSending || !input.trim() || !projectId}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded bg-primary p-1 text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {(sending || isSending) ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
          </button>
        </div>
      </div>
    </div>
  );
}
