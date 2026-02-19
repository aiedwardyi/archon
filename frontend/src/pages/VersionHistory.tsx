import { useState } from 'react';
import { Clock, RotateCcw, Check, ChevronRight, Info, FileText, ListChecks, Code, ArrowRight, Download, Monitor, Smartphone } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { versions } from '@/data/mockData';

const automatedTasks = [
  'Updated authentication middleware to support JWT and OAuth2',
  'Added Google Strategy in Passport.js configuration',
  'Generated database migrations for user identity links',
  'Updated front-end login component with social button',
  'Added environment variable documentation in README',
];

const artifactCards = [
  { label: 'Brief', description: '3 requirements, 7 success criteria', tab: 'Brief', icon: FileText },
  { label: 'Build Plan', description: '4 modules', tab: 'Plan', icon: ListChecks },
  { label: 'Code', description: '4 files generated', tab: 'Code', icon: Code },
];

export default function VersionHistory() {
  const [panelOpen, setPanelOpen] = useState(true);
  const [selectedVersion, setSelectedVersion] = useState(versions[0].id);
  const [viewport, setViewport] = useState<'desktop' | 'mobile'>('desktop');
  const navigate = useNavigate();

  const selected = versions.find((v) => v.id === selectedVersion)!;

  return (
    <div className="flex h-[calc(100vh-3rem)]">
      {/* Version Panel */}
      {panelOpen && (
        <aside className="w-72 border-r border-border bg-card flex flex-col flex-shrink-0">
          <div className="flex items-center justify-between border-b border-border px-3 py-2.5">
            <span className="text-xs font-semibold text-foreground">Version Timeline</span>
            <button onClick={() => setPanelOpen(false)} className="rounded p-0.5 text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
              <Clock className="h-3.5 w-3.5" />
            </button>
          </div>
          <div className="flex-1 overflow-auto">
            {versions.map((v) => {
              const isActive = v.id === selectedVersion;
              return (
                <button
                  key={v.id}
                  onClick={() => setSelectedVersion(v.id)}
                  className={`w-full text-left px-3 py-2.5 border-b border-border transition-colors ${
                    isActive ? 'bg-primary/5' : 'hover:bg-secondary/30 opacity-50 hover:opacity-80'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className={`h-2 w-2 rounded-full flex-shrink-0 ${
                      isActive ? 'bg-primary' : v.status === 'failed' ? 'bg-status-failed' : 'bg-muted-foreground/30'
                    }`} />
                    <span className={`text-xs font-semibold ${isActive ? 'text-primary' : 'text-foreground'}`}>
                      V{v.version}
                    </span>
                    <span className="ml-auto text-[10px] text-muted-foreground">{v.timestamp}</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground pl-4 truncate">{v.prompt.slice(0, 40)}</p>
                </button>
              );
            })}
          </div>
        </aside>
      )}

      {/* Main Content */}
      <div className="flex-1 overflow-auto px-8 py-6">
        {!panelOpen && (
          <button
            onClick={() => setPanelOpen(true)}
            className="mb-3 inline-flex items-center gap-1 rounded border border-border bg-card px-2 py-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            <Clock className="h-3 w-3" />
            Show History
          </button>
        )}

        <div className="max-w-2xl">
          {/* Version Header - outside card */}
          <div className="flex items-center gap-3 mb-5">
            <span className="rounded bg-primary/10 px-2 py-0.5 text-[11px] font-semibold font-mono text-primary uppercase tracking-wider">
              Version V{selected.version}
            </span>
            <span className="text-[11px] text-muted-foreground">{selected.timestamp}</span>
            <div className="ml-auto flex items-center gap-2">
              {selected.version < versions[0].version && (
                <button className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-[11px] font-medium text-primary-foreground hover:bg-primary/90 transition-colors">
                  <RotateCcw className="h-3 w-3" />
                  Restore to this version
                </button>
              )}
              <button className="inline-flex items-center gap-1 rounded-md border border-border bg-card px-3 py-1.5 text-[11px] font-medium text-muted-foreground hover:text-foreground transition-colors">
                <Download className="h-3 w-3" />
                Download Report
              </button>
            </div>
          </div>

          {/* Content card */}
          <div className="rounded border border-border bg-secondary/20 p-6 space-y-6">
            {/* User Prompt */}
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs font-semibold text-foreground">User Prompt</span>
              </div>
              <div className="rounded border border-border bg-card px-4 py-3">
                <p className="text-xs text-muted-foreground italic">"{selected.prompt}"</p>
              </div>
            </div>

            {/* What Was Built */}
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <Check className="h-3.5 w-3.5 text-status-complete" />
                <span className="text-xs font-semibold text-foreground">What Was Built</span>
              </div>
              <div className="rounded border border-border bg-card px-4 py-3 space-y-1.5">
                {automatedTasks.map((task, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <ChevronRight className="h-3 w-3 flex-shrink-0" />
                    {task}
                  </div>
                ))}
              </div>
            </div>

            {/* Build Artifacts */}
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <Code className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs font-semibold text-foreground">Build Artifacts</span>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {artifactCards.map((card) => (
                  <button
                    key={card.label}
                    onClick={() => navigate(`/artifacts?tab=${card.tab}`)}
                    className="group rounded border border-border bg-card p-3 text-left hover:border-primary/30 hover:bg-primary/5 transition-all"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-1.5">
                        <card.icon className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
                        <span className="text-xs font-semibold text-foreground">{card.label}</span>
                      </div>
                      <ArrowRight className="h-3 w-3 text-muted-foreground/0 group-hover:text-primary transition-all" />
                    </div>
                    <p className="text-[11px] text-muted-foreground">{card.description}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Live Preview */}
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <Monitor className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs font-semibold text-foreground">Live Preview</span>
              </div>
              <div className="rounded border border-border bg-card overflow-hidden">
                {/* Viewport toggle toolbar */}
                <div className="flex items-center justify-center px-4 py-2 border-b border-border">
                  <div className="flex items-center rounded-md border border-border bg-secondary/50 p-0.5">
                    <button
                      onClick={() => setViewport('desktop')}
                      className={`rounded p-1 transition-colors ${
                        viewport === 'desktop'
                          ? 'bg-card text-foreground shadow-sm'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                      title="Desktop view"
                    >
                      <Monitor className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setViewport('mobile')}
                      className={`rounded p-1 transition-colors ${
                        viewport === 'mobile'
                          ? 'bg-card text-foreground shadow-sm'
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                      title="Mobile view"
                    >
                      <Smartphone className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {/* Preview area */}
                <div className="bg-muted/50 flex items-center justify-center">
                  {viewport === 'desktop' ? (
                    <div className="w-full flex items-center justify-center py-16">
                      <div className="rounded-lg border-2 border-dashed border-border p-10 text-center max-w-md">
                        <Monitor className="h-8 w-8 text-muted-foreground/50 mx-auto mb-3" />
                        <p className="text-xs text-muted-foreground">
                          Live preview will appear here when your build is complete
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="w-[375px] max-h-[calc(100%-3rem)] aspect-[9/19.5] rounded-[1.5rem] border-[3px] border-border bg-background shadow-lg flex items-center justify-center overflow-hidden my-6">
                      <div className="text-center px-8">
                        <Smartphone className="h-8 w-8 text-muted-foreground/50 mx-auto mb-3" />
                        <p className="text-xs text-muted-foreground">
                          Live preview will appear here when your build is complete
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Validation Banner */}
            <div className="rounded border border-border bg-card px-4 py-3 flex items-start gap-2">
              <Info className="h-3.5 w-3.5 text-muted-foreground mt-0.5 flex-shrink-0" />
              <p className="text-xs text-muted-foreground leading-relaxed">
                This version passed all quality checks (14/14).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
