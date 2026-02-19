import { useState } from 'react';
import { Check, Loader2, Clock, ArrowRight, Send } from 'lucide-react';
import { pipelineAgents, logEntries } from '@/data/mockData';

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

export default function PipelineRun() {
  const [input, setInput] = useState('');

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="flex-1 overflow-auto px-5 py-5">
        {/* Pipeline Header */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-0.5">
            <h1 className="text-base font-semibold text-foreground">checkout-service</h1>
            <span className="rounded bg-secondary px-2 py-0.5 text-[10px] font-medium text-status-running status-pulse">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-status-running mr-1 align-middle" />
              Building...
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground">Version 14 · Started 32 seconds ago</p>
        </div>

        {/* Agent Pipeline */}
        <div className="flex items-stretch gap-0 mb-6">
          {pipelineAgents.map((agent, i) => (
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
              {i < pipelineAgents.length - 1 && (
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground mx-2 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>

        {/* Live Logs */}
        <div className="rounded border border-border bg-card">
          <div className="flex items-center justify-between border-b border-border px-3 py-2">
            <span className="text-[11px] font-medium text-foreground uppercase tracking-wider">Live Output</span>
            <span className="text-[11px] text-muted-foreground font-mono">{logEntries.length} entries</span>
          </div>
          <div className="p-3 font-mono text-[11px] space-y-0.5 max-h-[320px] overflow-auto">
            {logEntries.map((log, i) => (
              <div key={i} className="flex gap-2 leading-relaxed">
                <span className="text-muted-foreground/50 select-none w-14 flex-shrink-0">{log.timestamp}</span>
                <span className="text-foreground/80">{log.message}</span>
              </div>
            ))}
            <div className="flex items-center gap-2 text-muted-foreground pt-1">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span>Waiting for output...</span>
            </div>
          </div>
        </div>
      </div>

      {/* Input Bar */}
      <div className="border-t border-border bg-card px-5 py-2.5">
        <div className="relative max-w-3xl">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="What would you like to change?"
            className="w-full rounded border border-border bg-background pl-3 pr-10 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
          <button className="absolute right-1.5 top-1/2 -translate-y-1/2 rounded bg-primary p-1 text-primary-foreground hover:bg-primary/90 transition-colors">
            <Send className="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>
  );
}
