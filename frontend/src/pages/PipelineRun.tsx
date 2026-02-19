import { useState, useEffect, useRef } from 'react';
import { Check, Loader2, Clock, ArrowRight, Send } from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getExecutionStatus, iterateProject, startExecution, getProject, type ExecutionStatus, type Project } from '@/services/api';

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

export default function PipelineRun() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const projectId = searchParams.get('project') ? Number(searchParams.get('project')) : null;

  const [project, setProject] = useState<Project | null>(null);
  // null = not yet determined; we use this to avoid flashing stale state
  const [status, setStatus] = useState<ExecutionStatus | null>(null);
  // Whether the status we fetched actually belongs to this project
  const [statusOwned, setStatusOwned] = useState(false);
  const [input, setInput] = useState('');
  const [promptHistory, setPromptHistory] = useState<{ role: string; content: string }[]>([]);
  const [sending, setSending] = useState(false);
  const [startedAt, setStartedAt] = useState<Date | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Reset owned-status flag whenever we switch projects
  useEffect(() => {
    setStatusOwned(false);
    setStatus(null);
    setStartedAt(null);
    setElapsed(0);
  }, [projectId]);

  // Load project info
  useEffect(() => {
    if (!projectId) return;
    getProject(projectId)
      .then((p) => {
        setProject(p);
        // Pre-fill prompt history from the active head execution
        const head = p.executions?.find((e: { is_active_head: boolean }) => e.is_active_head);
        if (head?.prompt_history?.length) {
          setPromptHistory(head.prompt_history);
        }
      })
      .catch(console.error);
  }, [projectId]);

  // Poll execution status
  useEffect(() => {
    if (!projectId) return;

    function poll() {
      getExecutionStatus()
        .then((s) => {
          // Only treat the status as belonging to this project if:
          // 1. The backend says it's currently running for this project, OR
          // 2. We already know this project started a run this session (statusOwned is true)
          const belongsHere =
            s.status === 'RUNNING' && s.project_id === projectId;

          if (belongsHere) {
            setStatusOwned(true);
            setStatus(s);
          } else if (statusOwned) {
            // We owned it and now it finished — keep showing the result
            setStatus(s);
          }
          // Otherwise: stale data from a different project — ignore it

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
  }, [projectId, statusOwned]);

  // Elapsed timer while running
  useEffect(() => {
    if (status?.status !== 'RUNNING') return;
    if (!startedAt) setStartedAt(new Date());
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, [status?.status]);

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [status?.logs]);

  async function handleSend() {
    if (!input.trim() || !projectId || sending) return;
    const prompt = input.trim();
    setInput('');
    setSending(true);
    setStartedAt(new Date());
    setElapsed(0);
    setStatusOwned(true); // this project is now the owner of the pipeline

    const newHistory = [...promptHistory, { role: 'user', content: prompt }];
    setPromptHistory(newHistory);

    try {
      await iterateProject(projectId, prompt, newHistory);
      // Start polling
      if (!pollingRef.current) {
        pollingRef.current = setInterval(async () => {
          const s = await getExecutionStatus();
          setStatus(s);
          if (s.status !== 'RUNNING') {
            clearInterval(pollingRef.current!);
            pollingRef.current = null;
          }
        }, 2000);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setSending(false);
    }
  }

  const isRunning = status?.status === 'RUNNING' || sending;
  const currentStage = status?.currentStage || 'pm';
  // Only show logs if this project owns the status
  const logs = statusOwned ? (status?.logs || []) : [];
  const displayStatus = statusOwned ? status?.status : undefined;
  const versionLabel = isRunning ? '...' : (project?.execution_count ?? '—');

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="flex-1 overflow-auto px-5 py-5">

        {/* Pipeline Header */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-0.5">
            <h1 className="text-base font-semibold text-foreground">
              {project?.name || 'No project selected'}
            </h1>
            {isRunning && (
              <span className="rounded bg-secondary px-2 py-0.5 text-[10px] font-medium text-status-running">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-status-running mr-1 align-middle status-pulse" />
                Building...
              </span>
            )}
            {displayStatus === 'COMPLETED' && (
              <span className="rounded bg-secondary px-2 py-0.5 text-[10px] font-medium text-status-complete">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-status-complete mr-1 align-middle" />
                Done
              </span>
            )}
          </div>
          <p className="text-[11px] text-muted-foreground">
            {project ? `Version ${versionLabel}` : 'Select a project from Projects page'}
            {startedAt && isRunning && ` · Started ${elapsed}s ago`}
          </p>
        </div>

        {/* Agent Pipeline */}
        <div className="flex items-stretch gap-0 mb-6">
          {AGENTS.map((agent, i) => {
            const agSt = agentStatus(agent.id, currentStage, displayStatus || '');
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

        {/* Live Logs */}
        <div className="rounded border border-border bg-card">
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="text-[11px] font-medium text-foreground uppercase tracking-wider">Live Output</span>
            <span className="text-[11px] text-muted-foreground font-mono">{logs.length} entries</span>
          </div>
          <div className="p-3 font-mono text-[11px] space-y-0.5 max-h-[320px] overflow-auto">
            {logs.length === 0 && (
              <div className="text-muted-foreground italic">
                {projectId ? 'Type a prompt below to start building.' : 'Select a project to get started.'}
              </div>
            )}
            {logs.map((log, i) => (
              <div key={log.id || i} className="flex gap-2 leading-relaxed">
                <span className="text-muted-foreground/50 select-none w-20 flex-shrink-0 text-[10px]">
                  {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
                <span className="text-foreground/80">{log.message}</span>
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

        {/* Prompt history display */}
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

      {/* Chat Input Bar */}
      <div className="border-t border-border bg-card px-5 py-2.5">
        <div className="relative max-w-3xl">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={projectId ? 'What would you like to change?' : 'Select a project first'}
            disabled={isRunning || !projectId}
            className="w-full rounded border border-border bg-background pl-3 pr-10 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isRunning || !input.trim() || !projectId}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded bg-primary p-1 text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {sending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
          </button>
        </div>
      </div>
    </div>
  );
}
