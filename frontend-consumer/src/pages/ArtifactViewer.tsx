import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { FileCode, FolderOpen, ChevronRight, ChevronDown, ToggleLeft, ToggleRight, Shield, Play, CheckCircle2, Monitor, Smartphone, ExternalLink, Loader2 } from 'lucide-react';
import { API_BASE } from '@/lib/api';

const tabs = ['Brief', 'Plan', 'Code', 'Preview'] as const;
type Tab = typeof tabs[number];
type ViewportMode = 'desktop' | 'mobile';

type FileNode = { name: string; type: 'dir'; children: FileNode[] } | { name: string; type: 'file'; content?: string };

function FileTree({ items, depth = 0, onSelect }: { items: FileNode[]; depth?: number; onSelect: (node: FileNode) => void }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  return (
    <div>
      {items.map((item) => (
        <div key={item.name}>
          <button
            onClick={() => {
              if (item.type === 'dir') {
                setExpanded((s) => ({ ...s, [item.name]: !s[item.name] }));
              } else {
                onSelect(item);
              }
            }}
            className="w-full flex items-center gap-1.5 px-2 py-0.5 text-[11px] hover:bg-secondary/50 transition-colors rounded-sm text-foreground/80"
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
            <FileTree items={item.children} depth={depth + 1} onSelect={onSelect} />
          )}
        </div>
      ))}
    </div>
  );
}

function buildFileTree(files: { path: string; content: string }[]): FileNode[] {
  const root: FileNode[] = [];
  for (const f of files) {
    const parts = f.path.replace(/\\/g, '/').split('/');
    let current = root;
    for (let i = 0; i < parts.length; i++) {
      const name = parts[i];
      if (i === parts.length - 1) {
        current.push({ name, type: 'file', content: f.content });
      } else {
        let dir = current.find((n): n is FileNode & { type: 'dir' } => n.type === 'dir' && n.name === name + '/');
        if (!dir) {
          dir = { name: name + '/', type: 'dir', children: [] };
          current.push(dir);
        }
        current = dir.children;
      }
    }
  }
  return root;
}

const tabParamMap: Record<string, Tab> = { 'PRD': 'Brief', 'Brief': 'Brief', 'Plan': 'Plan', 'Code': 'Code', 'Preview': 'Preview' };

export default function ArtifactViewer() {
  const [searchParams] = useSearchParams();
  const rawTab = searchParams.get('tab') || 'Brief';
  const initialTab = tabParamMap[rawTab] || 'Brief';
  const [activeTab, setActiveTab] = useState<Tab>(initialTab);
  const [jsonView, setJsonView] = useState(false);
  const [viewport, setViewport] = useState<ViewportMode>('desktop');

  const [prd, setPrd] = useState<any>(null);
  const [plan, setPlan] = useState<any>(null);
  const [files, setFiles] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<{ name: string; content: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const projectId = sessionStorage.getItem('archon_project_id');
  const version = sessionStorage.getItem('archon_version');

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab) {
      const mapped = tabParamMap[tab];
      if (mapped) setActiveTab(mapped);
    }
  }, [searchParams]);

  useEffect(() => {
    if (!projectId || !version) return;

    if (activeTab === 'Brief' && !prd) {
      setLoading(true);
      fetch(`${API_BASE}/api/prd?project_id=${projectId}&version=${version}`)
        .then(r => r.json())
        .then(data => setPrd(data.prd || data))
        .catch(console.error)
        .finally(() => setLoading(false));
    }

    if (activeTab === 'Plan' && !plan) {
      setLoading(true);
      fetch(`${API_BASE}/api/plan?project_id=${projectId}&version=${version}`)
        .then(r => r.json())
        .then(data => setPlan(data.plan || data))
        .catch(console.error)
        .finally(() => setLoading(false));
    }

    if (activeTab === 'Code' && files.length === 0) {
      setLoading(true);
      fetch(`${API_BASE}/api/projects/${projectId}/versions/${version}/files`)
        .then(r => r.json())
        .then(data => {
          const tree = buildFileTree(data.files || []);
          setFiles(tree);
        })
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [activeTab, projectId, version]);

  const previewUrl = projectId && version
    ? `${API_BASE}/api/preview/${projectId}/${version}`
    : '';

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      {/* Top toolbar */}
      <div className="border-b border-border bg-card px-5 py-1.5 flex items-center">
        <div className="flex items-center gap-1 text-[11px] font-mono">
          <span className="rounded bg-secondary px-1.5 py-0.5 text-muted-foreground font-medium">Requirements</span>
          <span className="text-muted-foreground">&rarr;</span>
          <span className="rounded bg-secondary px-1.5 py-0.5 text-primary font-medium">Architecture</span>
          <span className="text-muted-foreground">&rarr;</span>
          <span className="rounded bg-secondary px-1.5 py-0.5 text-accent-foreground font-medium">Code</span>
        </div>
        <span className="h-3 w-px bg-border ml-2" />
        <span className="rounded border border-status-complete/20 bg-status-complete/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-status-complete inline-flex items-center gap-1 ml-2">
          <Play className="h-2.5 w-2.5" /> Reproducible
        </span>
        <span className="rounded border border-status-running/20 bg-status-running/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-status-running inline-flex items-center gap-1 ml-1">
          <Shield className="h-2.5 w-2.5" /> Verified
        </span>
        {version && (
          <span className="rounded border border-primary/20 bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-primary inline-flex items-center gap-1 ml-1">
            <CheckCircle2 className="h-2.5 w-2.5" /> v{version}
          </span>
        )}

        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setJsonView(!jsonView)}
            className="inline-flex items-center gap-1 rounded border border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
          >
            {jsonView ? <ToggleRight className="h-3 w-3 text-primary" /> : <ToggleLeft className="h-3 w-3" />}
            Raw Data
          </button>
          <a
            href={previewUrl || '#'}
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
        {loading && (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {activeTab === 'Brief' && !loading && prd && !jsonView && (
          <div className="overflow-auto p-5">
            <h2 className="text-sm font-semibold text-foreground mb-0.5">{prd.document_title || 'Untitled'}</h2>
            <p className="text-[11px] text-muted-foreground mb-5">v{prd.version || '1'}</p>

            {prd.user_stories && prd.user_stories.length > 0 && (
              <>
                <h3 className="text-xs font-semibold text-foreground mb-2">What We're Building</h3>
                <div className="space-y-1.5 mb-5">
                  {prd.user_stories.map((s: string, i: number) => (
                    <div key={i} className="rounded border border-border bg-card p-2.5 text-xs text-foreground/80">{s}</div>
                  ))}
                </div>
              </>
            )}

            {prd.acceptance_criteria && prd.acceptance_criteria.length > 0 && (
              <>
                <h3 className="text-xs font-semibold text-foreground mb-2">Success Criteria</h3>
                <div className="space-y-1">
                  {prd.acceptance_criteria.map((c: string, i: number) => (
                    <div key={i} className="flex items-start gap-1.5 text-xs text-foreground/80">
                      <CheckCircle2 className="h-3.5 w-3.5 text-status-complete mt-0.5 flex-shrink-0" />
                      {c}
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'Brief' && !loading && prd && jsonView && (
          <div className="overflow-auto p-5 bg-surface-sunken h-full">
            <pre className="font-mono text-[11px] leading-relaxed text-foreground/80 whitespace-pre-wrap">
              {JSON.stringify(prd, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === 'Plan' && !loading && plan && !jsonView && (
          <div className="overflow-auto p-5">
            <h2 className="text-sm font-semibold text-foreground mb-0.5">Build Plan</h2>
            <p className="text-[11px] text-muted-foreground mb-5">{(plan.milestones || []).length} milestones</p>

            <div className="space-y-2">
              {(plan.milestones || []).map((m: any, mi: number) => (
                <div key={mi} className="rounded border border-border bg-card p-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-medium text-foreground">{m.title || m.name || `Milestone ${mi + 1}`}</span>
                  </div>
                  {m.tasks && (
                    <div className="space-y-1">
                      {m.tasks.map((t: any, ti: number) => (
                        <div key={ti} className="flex items-center gap-2 text-[11px] text-muted-foreground">
                          <ChevronRight className="h-2.5 w-2.5 flex-shrink-0" />
                          <span>{t.description || t.title || `Task ${ti + 1}`}</span>
                          {t.output_files && (
                            <div className="flex gap-1 ml-auto">
                              {t.output_files.map((f: string) => (
                                <span key={f} className="rounded bg-secondary px-1.5 py-0.5 text-[10px] font-mono">{f}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'Plan' && !loading && plan && jsonView && (
          <div className="overflow-auto p-5 bg-surface-sunken h-full">
            <pre className="font-mono text-[11px] leading-relaxed text-foreground/80 whitespace-pre-wrap">
              {JSON.stringify(plan, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === 'Code' && !loading && !jsonView && (
          <div className="flex h-full">
            <aside className="w-52 border-r border-border bg-card overflow-auto py-1.5 flex-shrink-0">
              <FileTree items={files} onSelect={(node) => {
                if (node.type === 'file' && 'content' in node) {
                  setSelectedFile({ name: node.name, content: node.content || '' });
                }
              }} />
            </aside>
            <div className="flex-1 overflow-auto bg-surface-sunken p-3">
              {selectedFile ? (
                <>
                  <div className="mb-1.5 flex items-center gap-2">
                    <span className="text-[11px] font-mono text-muted-foreground">{selectedFile.name}</span>
                  </div>
                  <pre className="font-mono text-[11px] leading-relaxed text-foreground/90 whitespace-pre-wrap">{selectedFile.content}</pre>
                </>
              ) : (
                <p className="text-xs text-muted-foreground p-4">Select a file to view its contents</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'Code' && !loading && jsonView && (
          <div className="overflow-auto p-5 bg-surface-sunken h-full">
            <pre className="font-mono text-[11px] leading-relaxed text-foreground/80 whitespace-pre-wrap">
              {JSON.stringify(files, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === 'Preview' && (
          <div className="flex flex-col h-full">
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
                href={previewUrl || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="absolute right-5 inline-flex items-center gap-1 rounded border border-border px-2 py-0.5 text-[11px] text-muted-foreground hover:text-foreground transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                Open in new tab
              </a>
            </div>

            <div className="flex-1 bg-muted/50 flex items-start justify-center overflow-auto">
              {viewport === 'desktop' ? (
                <iframe src={previewUrl} className="w-full h-full border-0" title="preview" />
              ) : (
                <div className="w-[375px] h-[812px] rounded-[1.5rem] border-[3px] border-border bg-background shadow-lg overflow-hidden my-6">
                  <iframe src={previewUrl} width="375" height="812" className="border-0" title="preview" />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
