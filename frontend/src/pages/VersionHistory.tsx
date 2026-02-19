import { useState, useEffect } from 'react';
import { Clock, RotateCcw, Check, ChevronRight, FileText, ListChecks, Code, ArrowRight, Download, Monitor, Smartphone, Loader2 } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { getVersions, restoreVersion, type Execution } from '@/services/api';

const artifactTabs = [
  { label: 'Brief', tab: 'Brief', icon: FileText, description: 'Requirements & success criteria' },
  { label: 'Build Plan', tab: 'Plan', icon: ListChecks, description: 'Architecture modules' },
  { label: 'Code', tab: 'Code', icon: Code, description: 'Generated files' },
];

function formatTs(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  });
}

export default function VersionHistory() {
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get('project') ? Number(searchParams.get('project')) : null;
  const navigate = useNavigate();

  const [versions, setVersions] = useState<Execution[]>([]);
  const [projectName, setProjectName] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [viewport, setViewport] = useState<'desktop' | 'mobile'>('desktop');
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState(false);

  useEffect(() => {
    if (!projectId) { setLoading(false); return; }
    getVersions(projectId)
      .then((data) => {
        setVersions(data.versions);
        setProjectName(data.project_name);
        // Select the active head by default
        const head = data.versions.find((v) => v.is_active_head) || data.versions[0];
        if (head) setSelectedId(head.id);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [projectId]);

  const selected = versions.find((v) => v.id === selectedId);
  const isHead = selected?.is_active_head;

  async function handleRestore() {
    if (!selected || isHead) return;
    setRestoring(true);
    try {
      await restoreVersion(selected.id);
      // Refresh versions list
      const data = await getVersions(projectId!);
      setVersions(data.versions);
    } catch (e) {
      console.error(e);
    } finally {
      setRestoring(false);
    }
  }

  // Get the last user prompt for a version
  function getPrompt(execution: Execution): string {
    const history = execution.prompt_history || [];
    const last = [...history].reverse().find((t) => t.role === 'user');
    return last?.content || '(no prompt recorded)';
  }

  return (
    <div className="flex h-[calc(100vh-3rem)]">
      {/* Version Timeline Panel */}
      <aside className="w-72 border-r border-border bg-card flex flex-col flex-shrink-0">
        <div className="flex items-center justify-between border-b border-border px-3 py-2.5">
          <span className="text-xs font-semibold text-foreground">Version Timeline</span>
          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
        </div>
        <div className="flex-1 overflow-auto">
          {loading && (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin mr-2" />
              <span className="text-[11px]">Loading...</span>
            </div>
          )}
          {!loading && !projectId && (
            <p className="text-[11px] text-muted-foreground px-3 py-4">No project selected. Open from Projects page.</p>
          )}
          {!loading && projectId && versions.length === 0 && (
            <p className="text-[11px] text-muted-foreground px-3 py-4">No versions yet. Run the pipeline to create one.</p>
          )}
          {versions.map((v) => {
            const isActive = v.id === selectedId;
            const prompt = getPrompt(v);
            return (
              <button
                key={v.id}
                onClick={() => setSelectedId(v.id)}
                className={`w-full text-left px-3 py-2.5 border-b border-border transition-colors ${
                  isActive ? 'bg-primary/5' : 'hover:bg-secondary/30 opacity-60 hover:opacity-90'
                }`}
              >
                <div className="flex items-center gap-2 mb-0.5">
                  <span className={`h-2 w-2 rounded-full flex-shrink-0 ${
                    v.is_active_head ? 'bg-primary' : v.status === 'error' ? 'bg-status-failed' : 'bg-muted-foreground/30'
                  }`} />
                  <span className={`text-xs font-semibold ${isActive ? 'text-primary' : 'text-foreground'}`}>
                    V{v.version}
                  </span>
                  <span className="ml-auto text-[10px] text-muted-foreground">{formatTs(v.created_at)}</span>
                </div>
                <p className="text-[11px] text-muted-foreground pl-4 truncate">{prompt.slice(0, 42)}</p>
              </button>
            );
          })}
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 overflow-auto px-8 py-6">
        {!selected && !loading && (
          <p className="text-xs text-muted-foreground">Select a version from the timeline.</p>
        )}

        {selected && (
          <div className="max-w-2xl">
            {/* Version Header */}
            <div className="flex items-center gap-3 mb-5">
              <span className="rounded bg-primary/10 px-2 py-0.5 text-[11px] font-semibold font-mono text-primary uppercase tracking-wider">
                Version V{selected.version}
              </span>
              <span className="text-[11px] text-muted-foreground">{formatTs(selected.created_at)}</span>
              <div className="ml-auto flex items-center gap-2">
                {!isHead && (
                  <button
                    onClick={handleRestore}
                    disabled={restoring}
                    className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-[11px] font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  >
                    {restoring ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3" />}
                    Restore to this version
                  </button>
                )}
                <button className="inline-flex items-center gap-1 rounded-md border border-border bg-card px-3 py-1.5 text-[11px] font-medium text-muted-foreground hover:text-foreground transition-colors">
                  <Download className="h-3 w-3" />
                  Download Report
                </button>
              </div>
            </div>

            {/* Content Card */}
            <div className="rounded border border-border bg-secondary/20 p-6 space-y-6">
              {/* User Prompt */}
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs font-semibold text-foreground">User Prompt</span>
                </div>
                <div className="rounded border border-border bg-card px-4 py-3">
                  <p className="text-xs text-muted-foreground italic">"{getPrompt(selected)}"</p>
                </div>
              </div>

              {/* What Was Built */}
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <Check className="h-3.5 w-3.5 text-status-complete" />
                  <span className="text-xs font-semibold text-foreground">What Was Built</span>
                </div>
                <div className="rounded border border-border bg-card px-4 py-3">
                  {selected.status === 'success' ? (
                    <p className="text-xs text-muted-foreground">
                      Pipeline completed successfully. View artifacts for details.
                    </p>
                  ) : selected.status === 'error' ? (
                    <p className="text-xs text-status-failed">{selected.error_message || 'Pipeline failed.'}</p>
                  ) : (
                    <p className="text-xs text-muted-foreground italic">Running...</p>
                  )}
                </div>
              </div>

              {/* Build Artifacts */}
              <div>
                <div className="flex items-center gap-1.5 mb-3">
                  <Code className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs font-semibold text-foreground">Build Artifacts</span>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {artifactTabs.map((card) => (
                    <button
                      key={card.label}
                      onClick={() => navigate(`/artifacts?tab=${card.tab}&project=${projectId}`)}
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
                  <div className="flex items-center justify-center px-4 py-2 border-b border-border">
                    <div className="flex items-center rounded-md border border-border bg-secondary/50 p-0.5">
                      <button
                        onClick={() => setViewport('desktop')}
                        className={`rounded p-1 transition-colors ${viewport === 'desktop' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                      >
                        <Monitor className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => setViewport('mobile')}
                        className={`rounded p-1 transition-colors ${viewport === 'mobile' ? 'bg-card text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
                      >
                        <Smartphone className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                  <div className="bg-muted/50 flex items-center justify-center">
                    {viewport === 'desktop' ? (
                      <div className="w-full flex items-center justify-center py-16">
                        <div className="rounded-lg border-2 border-dashed border-border p-10 text-center max-w-md">
                          <Monitor className="h-8 w-8 text-muted-foreground/50 mx-auto mb-3" />
                          <p className="text-xs text-muted-foreground">Live preview will appear here when your build is complete</p>
                        </div>
                      </div>
                    ) : (
                      <div className="w-[375px] h-[580px] rounded-[1.5rem] border-[3px] border-border bg-background shadow-lg flex items-center justify-center overflow-hidden my-6">
                        <div className="text-center px-8">
                          <Smartphone className="h-8 w-8 text-muted-foreground/50 mx-auto mb-3" />
                          <p className="text-xs text-muted-foreground">Live preview will appear here when your build is complete</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
