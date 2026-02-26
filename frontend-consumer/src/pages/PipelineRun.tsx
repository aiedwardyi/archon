import { useState, useEffect, useRef } from 'react';
import { Check, Loader2, Clock, ArrowRight, Send } from 'lucide-react';
import { sendChat, iterateProject, fetchExecutionStatus } from '@/lib/api';

interface AgentState {
  id: string;
  name: string;
  description: string;
  status: 'complete' | 'running' | 'pending';
  duration: string;
}

interface LogEntry {
  message: string;
  timestamp?: string;
}

const statusIcon = (status: string) => {
  if (status === 'complete') return <Check className="h-3.5 w-3.5 text-status-complete" />;
  if (status === 'running') return <Loader2 className="h-3.5 w-3.5 text-status-running animate-spin" />;
  return <Clock className="h-3.5 w-3.5 text-muted-foreground" />;
};

const statusLabel = (status: string) => {
  if (status === 'complete') return 'Done';
  if (status === 'running') return 'Building...';
  return status;
};

function stageToAgents(currentStage: string, pipelineStatus: string): AgentState[] {
  const stages = ['pm', 'planner', 'engineer'];
  const names = ['Requirements Agent', 'Architecture Agent', 'Build Agent'];
  const descs = ['Understands your request', 'Plans the build', 'Writes your code'];
  const currentIdx = stages.indexOf(currentStage);

  return stages.map((s, i) => {
    let status: AgentState['status'] = 'pending';
    if (pipelineStatus === 'COMPLETED' || pipelineStatus === 'FAILED') {
      status = i <= currentIdx ? 'complete' : 'pending';
    } else if (i < currentIdx) {
      status = 'complete';
    } else if (i === currentIdx) {
      status = 'running';
    }
    return { id: s, name: names[i], description: descs[i], status, duration: status === 'complete' ? 'done' : status === 'running' ? '...' : '' };
  });
}

export default function PipelineRun() {
  const [input, setInput] = useState('');
  const [chatReply, setChatReply] = useState('');
  const [agents, setAgents] = useState<AgentState[]>([
    { id: 'pm', name: 'Requirements Agent', description: 'Understands your request', status: 'pending', duration: '' },
    { id: 'planner', name: 'Architecture Agent', description: 'Plans the build', status: 'pending', duration: '' },
    { id: 'engineer', name: 'Build Agent', description: 'Writes your code', status: 'pending', duration: '' },
  ]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [pipelineStatus, setPipelineStatus] = useState<string>('IDLE');
  const [sending, setSending] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const promptHistoryRef = useRef<any[]>([]);

  const projectId = Number(sessionStorage.getItem('archon_project_id'));
  const projectName = sessionStorage.getItem('archon_project_name') || 'Untitled';

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => () => stopPolling(), []);

  const startPolling = () => {
    stopPolling();
    pollingRef.current = setInterval(async () => {
      try {
        const data = await fetchExecutionStatus();
        const stage = data.currentStage || 'pm';
        const status = data.status || 'RUNNING';
        setAgents(stageToAgents(stage, status));
        setLogs((data.logs || []).map((l: any) => ({
          message: typeof l === 'string' ? l : l.message || '',
          timestamp: l.timestamp || '',
        })));
        setPipelineStatus(status);
        if (status === 'COMPLETED' || status === 'FAILED') {
          stopPolling();
          if (data.execution_id) sessionStorage.setItem('archon_execution_id', String(data.execution_id));
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    }, 2000);
  };

  const handleSend = async () => {
    const msg = input.trim();
    if (!msg || sending || !projectId) return;
    setSending(true);
    setChatReply('');

    try {
      promptHistoryRef.current.push({ role: 'user', content: msg });
      const chatRes = await sendChat(projectId, msg);

      if (chatRes.response_type === 'chat') {
        setChatReply(chatRes.message);
        setSending(false);
        return;
      }

      // response_type === 'build'
      setPipelineStatus('RUNNING');
      setAgents(stageToAgents('pm', 'RUNNING'));
      setLogs([]);

      const iterRes = await iterateProject(projectId, msg, promptHistoryRef.current);
      if (iterRes.execution_id) sessionStorage.setItem('archon_execution_id', String(iterRes.execution_id));
      if (iterRes.version) sessionStorage.setItem('archon_version', String(iterRes.version));

      startPolling();
    } catch (e) {
      console.error('Send error:', e);
      setChatReply('Something went wrong. Please try again.');
    } finally {
      setSending(false);
      setInput('');
    }
  };

  const isRunning = pipelineStatus === 'RUNNING';

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="flex-1 overflow-auto px-5 py-5">
        {/* Pipeline Header */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-0.5">
            <h1 className="text-base font-semibold text-foreground">{projectName}</h1>
            {isRunning && (
              <span className="rounded bg-secondary px-2 py-0.5 text-[10px] font-medium text-status-running status-pulse">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-status-running mr-1 align-middle" />
                Building...
              </span>
            )}
            {pipelineStatus === 'COMPLETED' && (
              <span className="rounded bg-secondary px-2 py-0.5 text-[10px] font-medium text-status-complete">
                Completed
              </span>
            )}
            {pipelineStatus === 'FAILED' && (
              <span className="rounded bg-secondary px-2 py-0.5 text-[10px] font-medium text-status-failed">
                Failed
              </span>
            )}
          </div>
          <p className="text-[11px] text-muted-foreground">Project #{projectId}</p>
        </div>

        {/* Chat Reply */}
        {chatReply && (
          <div className="mb-4 rounded border border-border bg-card px-4 py-3">
            <p className="text-xs text-foreground/80">{chatReply}</p>
          </div>
        )}

        {/* Agent Pipeline */}
        {pipelineStatus !== 'IDLE' && (
          <div className="flex items-stretch gap-0 mb-6">
            {agents.map((agent, i) => (
              <div key={agent.id} className="flex items-center">
                <div className={`rounded border p-3 min-w-[200px] transition-all ${
                  agent.status === 'running'
                    ? 'border-status-running/40 bg-status-running/5'
                    : agent.status === 'complete'
                    ? 'border-border bg-card'
                    : 'border-border bg-secondary/30'
                }`}>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    {statusIcon(agent.status)}
                    <span className="text-xs font-medium text-foreground">{agent.name}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground mb-1.5">{agent.description}</p>
                  <div className="flex items-center gap-2">
                    <span className={`text-[11px] font-mono ${
                      agent.status === 'running' ? 'text-status-running' : 'text-muted-foreground'
                    }`}>
                      {agent.duration}
                    </span>
                    <span className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                      {statusLabel(agent.status)}
                    </span>
                  </div>
                </div>
                {i < agents.length - 1 && (
                  <ArrowRight className="h-3.5 w-3.5 text-muted-foreground mx-2 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        )}

        {/* Live Logs */}
        {logs.length > 0 && (
          <div className="rounded border border-border bg-card">
            <div className="flex items-center justify-between border-b border-border px-3 py-2">
              <span className="text-[11px] font-medium text-foreground uppercase tracking-wider">Live Output</span>
              <span className="text-[11px] text-muted-foreground font-mono">{logs.length} entries</span>
            </div>
            <div className="p-3 font-mono text-[11px] space-y-0.5 max-h-[320px] overflow-auto">
              {logs.map((log, i) => (
                <div key={i} className="flex gap-2 leading-relaxed">
                  <span className="text-muted-foreground/50 select-none w-14 flex-shrink-0">{log.timestamp || ''}</span>
                  <span className="text-foreground/80">{log.message}</span>
                </div>
              ))}
              {isRunning && (
                <div className="flex items-center gap-2 text-muted-foreground pt-1">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>Waiting for output...</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="border-t border-border bg-card px-5 py-2.5">
        <div className="relative max-w-3xl">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="What would you like to change?"
            disabled={isRunning}
            className="w-full rounded border border-border bg-background pl-3 pr-10 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isRunning || sending}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded bg-primary p-1 text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            {sending ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
          </button>
        </div>
      </div>
    </div>
  );
}
