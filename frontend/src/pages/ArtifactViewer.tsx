import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FileCode, FolderOpen, ChevronRight, ChevronDown, ToggleLeft, ToggleRight, Shield, Play, CheckCircle2, Monitor, Smartphone, ExternalLink } from 'lucide-react';
import { sampleCode, samplePRD, samplePlan, artifactFiles, type FileNode } from '@/data/mockData';

const tabs = ['Brief', 'Plan', 'Code', 'Tasks', 'Logs', 'Preview'] as const;
type Tab = typeof tabs[number];
type ViewportMode = 'desktop' | 'mobile';

function FileTree({ items, depth = 0 }: { items: FileNode[]; depth?: number }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({ 'src/': true, 'handlers/': true });

  return (
    <div>
      {items.map((item) => (
        <div key={item.name}>
          <button
            onClick={() => item.type === 'dir' && setExpanded((s) => ({ ...s, [item.name]: !s[item.name] }))}
            className={`w-full flex items-center gap-1.5 px-2 py-0.5 text-[11px] hover:bg-secondary/50 transition-colors rounded-sm ${
              item.type === 'file' && item.name === 'payment.ts' ? 'bg-primary/10 text-primary' : 'text-foreground/80'
            }`}
            style={{ paddingLeft: `${depth * 12 + 8}px` }}
          >
            {item.type === 'dir' ? (
              expanded[item.name] ? <ChevronDown className="h-2.5 w-2.5 text-muted-foreground" /> : <ChevronRight className="h-2.5 w-2.5 text-muted-foreground" />
            ) : (
              <FileCode className="h-2.5 w-2.5 text-muted-foreground" />
            )}
            {item.type === 'dir' && <FolderOpen className="h-2.5 w-2.5 text-primary/60" />}
            <span className="font-mono">{item.name}</span>
          </button>
          {item.type === 'dir' && expanded[item.name] && (
            <FileTree items={item.children} depth={depth + 1} />
          )}
        </div>
      ))}
    </div>
  );
}

const tabParamMap: Record<string, Tab> = { 'PRD': 'Brief', 'Brief': 'Brief', 'Plan': 'Plan', 'Code': 'Code', 'Tasks': 'Tasks', 'Logs': 'Logs', 'Preview': 'Preview' };

export default function ArtifactViewer() {
  const [searchParams] = useSearchParams();
  const rawTab = searchParams.get('tab') || 'Brief';
  const initialTab = tabParamMap[rawTab] || 'Brief';
  const [activeTab, setActiveTab] = useState<Tab>(initialTab);
  const [jsonView, setJsonView] = useState(false);
  const [viewport, setViewport] = useState<ViewportMode>('desktop');

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab) {
      const mapped = tabParamMap[tab];
      if (mapped) setActiveTab(mapped);
    }
  }, [searchParams]);

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      {/* Top toolbar */}
      <div className="border-b border-border bg-card px-5 py-1.5 flex items-center">
        {/* Agent Chain */}
        <div className="flex items-center gap-1 text-[11px] font-mono">
          <span className="rounded bg-secondary px-1.5 py-0.5 text-muted-foreground font-medium">Requirements</span>
          <span className="text-muted-foreground">→</span>
          <span className="rounded bg-secondary px-1.5 py-0.5 text-primary font-medium">Architecture</span>
          <span className="text-muted-foreground">→</span>
          <span className="rounded bg-secondary px-1.5 py-0.5 text-accent-foreground font-medium">Code</span>
        </div>
        <span className="h-3 w-px bg-border ml-2" />
        <span className="rounded border border-status-complete/20 bg-status-complete/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-status-complete inline-flex items-center gap-1 ml-2">
          <Play className="h-2.5 w-2.5" /> Reproducible
        </span>
        <span className="rounded border border-status-running/20 bg-status-running/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-status-running inline-flex items-center gap-1 ml-1">
          <Shield className="h-2.5 w-2.5" /> Verified
        </span>
        <span className="rounded border border-primary/20 bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-primary inline-flex items-center gap-1 ml-1">
          <CheckCircle2 className="h-2.5 w-2.5" /> v14
        </span>

        {/* Right side controls */}
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setJsonView(!jsonView)}
            className="inline-flex items-center gap-1 rounded border border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            {jsonView ? <ToggleRight className="h-3 w-3 text-primary" /> : <ToggleLeft className="h-3 w-3" />}
            Raw Data
          </button>
          <a
            href={window.location.href}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 rounded border border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-border bg-card px-5">
        <div className="flex gap-0">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden h-full">
        {activeTab === 'Code' && !jsonView && (
          <div className="flex h-full">
            <aside className="w-52 border-r border-border bg-card overflow-auto py-1.5 flex-shrink-0">
              <FileTree items={artifactFiles} />
            </aside>
            <div className="flex-1 overflow-auto bg-surface-sunken p-3">
              <div className="mb-1.5 flex items-center gap-2">
                <span className="text-[11px] font-mono text-muted-foreground">src/handlers/payment.ts</span>
                <span className="text-[11px] text-muted-foreground">· 89 lines</span>
              </div>
              <pre className="font-mono text-[11px] leading-relaxed text-foreground/90 whitespace-pre-wrap">{sampleCode}</pre>
            </div>
          </div>
        )}

        {activeTab === 'Code' && jsonView && (
          <div className="overflow-auto p-5 bg-surface-sunken h-full">
            <pre className="font-mono text-[11px] leading-relaxed text-foreground/80 whitespace-pre-wrap">
              {JSON.stringify({ file: 'src/handlers/payment.ts', language: 'typescript', lines: 89, content: sampleCode }, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === 'Brief' && !jsonView && (
          <div className="overflow-auto p-5">
            <h2 className="text-sm font-semibold text-foreground mb-0.5">{samplePRD.title}</h2>
            <p className="text-[11px] text-muted-foreground mb-5">v{samplePRD.version} · Generated by {samplePRD.author}</p>

            <h3 className="text-xs font-semibold text-foreground mb-2">What We're Building</h3>
            <div className="space-y-1.5 mb-5">
              {samplePRD.userStories.map((s, i) => (
                <div key={i} className="rounded border border-border bg-card p-2.5 text-xs text-foreground/80">{s}</div>
              ))}
            </div>

            <h3 className="text-xs font-semibold text-foreground mb-2">Success Criteria</h3>
            <div className="space-y-1">
              {samplePRD.acceptanceCriteria.map((c, i) => (
                <div key={i} className="flex items-start gap-1.5 text-xs text-foreground/80">
                  <CheckCircle2 className="h-3.5 w-3.5 text-status-complete mt-0.5 flex-shrink-0" />
                  {c}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'Brief' && jsonView && (
          <div className="overflow-auto p-5 bg-surface-sunken h-full">
            <pre className="font-mono text-[11px] leading-relaxed text-foreground/80 whitespace-pre-wrap">
              {JSON.stringify(samplePRD, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === 'Plan' && !jsonView && (
          <div className="overflow-auto p-5">
            <h2 className="text-sm font-semibold text-foreground mb-0.5">Build Plan</h2>
            <p className="text-[11px] text-muted-foreground mb-5">{samplePlan.modules.length} modules · Est. {samplePlan.estimatedDuration}</p>

            <div className="space-y-2">
              {samplePlan.modules.map((m) => (
                <div key={m.name} className="rounded border border-border bg-card p-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-medium text-foreground">{m.name}</span>
                  </div>
                  <div className="flex flex-wrap gap-1 mb-1.5">
                    {m.files.map((f) => (
                      <span key={f} className="rounded bg-secondary px-1.5 py-0.5 text-[11px] font-mono text-muted-foreground">{f}</span>
                    ))}
                  </div>
                  {m.dependencies.length > 0 && (
                    <div className="flex items-center gap-1">
                      <span className="text-[10px] text-muted-foreground uppercase tracking-wider">Uses:</span>
                      {m.dependencies.map((d) => (
                        <span key={d} className="text-[11px] text-primary/70 font-mono">{d}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'Plan' && jsonView && (
          <div className="overflow-auto p-5 bg-surface-sunken h-full">
            <pre className="font-mono text-[11px] leading-relaxed text-foreground/80 whitespace-pre-wrap">
              {JSON.stringify(samplePlan, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === 'Tasks' && (
          <div className="overflow-auto p-5 max-w-3xl">
            <h2 className="text-sm font-semibold text-foreground mb-3">Build Tasks</h2>
            <div className="space-y-1.5">
              {['Implement webhook endpoint with signature verification', 'Create event processor for payment intents', 'Add idempotency middleware', 'Set up dead-letter queue for failed events'].map((t, i) => (
                <div key={i} className="flex items-center gap-2 rounded border border-border bg-card p-2.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-status-complete flex-shrink-0" />
                  <span className="text-xs text-foreground">{t}</span>
                  <span className="ml-auto text-[11px] font-mono text-muted-foreground">T-{i + 1}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'Logs' && (
          <div className="overflow-auto p-5 bg-surface-sunken h-full">
            <div className="font-mono text-[11px] space-y-0.5">
              {[
                '[14:32:01] Analyzing your request...',
                '[14:32:04] Requirements document created',
                '[14:32:05] Requirements verified ✓',
                '[14:32:06] Planning the build...',
                '[14:32:09] Created 4 build tasks',
                '[14:32:10] Resolving build dependencies...',
                '[14:32:11] Build plan ready — 4 files',
                '[14:32:12] Writing your code...',
                '[14:32:15] Created payment handler ✓',
                '[14:32:18] Created webhook handler ✓',
                '[14:32:20] Running quality checks...',
                '[14:32:22] Creating transaction model...',
              ].map((line, i) => (
                <div key={i} className="leading-relaxed text-foreground/80">
                  {line}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'Preview' && (
          <div className="flex flex-col h-full">
            {/* Preview toolbar */}
            <div className="flex items-center justify-center px-5 py-2 border-b border-border bg-card relative">
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
              <a
                href="#"
                target="_blank"
                rel="noopener noreferrer"
                className="absolute right-5 inline-flex items-center gap-1 rounded border border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                Open in new tab
              </a>
            </div>

            {/* Preview area */}
            <div className="flex-1 bg-muted/50 flex items-start justify-center overflow-auto">
              {viewport === 'desktop' ? (
                <div className="h-full w-full flex items-center justify-center bg-background">
                  <div className="rounded-lg border-2 border-dashed border-border p-10 text-center max-w-md">
                    <Monitor className="h-8 w-8 text-muted-foreground/50 mx-auto mb-3" />
                    <p className="text-xs text-muted-foreground">
                      Live preview will appear here when your build is complete
                    </p>
                  </div>
                </div>
              ) : (
                <div className="w-[375px] h-[812px] rounded-[1.5rem] border-[3px] border-border bg-background shadow-lg flex items-center justify-center overflow-hidden my-6">
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
        )}
      </div>
    </div>
  );
}
