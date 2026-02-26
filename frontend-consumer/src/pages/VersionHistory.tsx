import { useState, useEffect } from 'react';
import { Clock, RotateCcw, Check, ChevronRight, Info, FileText, ListChecks, Code, ArrowRight, Download, Monitor, Smartphone, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { fetchVersions, restoreVersion, API_BASE } from '@/lib/api';

interface VersionEntry {
  id: number;
  version: number;
  prompt: string;
  timestamp: string;
  status: 'completed' | 'failed' | 'running' | 'pending';
}

function mapStatus(raw: string): VersionEntry['status'] {
  if (raw === 'success') return 'completed';
  if (raw === 'error') return 'failed';
  if (raw === 'running' || raw === 'in_progress' || raw === 'pending') return raw as any;
  return raw as any;
}

function extractPrompt(promptHistory: any[]): string {
  if (!promptHistory || promptHistory.length === 0) return '(no prompt)';
  for (let i = promptHistory.length - 1; i >= 0; i--) {
    if (promptHistory[i].role === 'user') return promptHistory[i].content;
  }
  return promptHistory[0]?.content || '(no prompt)';
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
    ', ' + d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

const artifactCards = [
  { label: 'Brief', description: 'Requirements & criteria', tab: 'Brief', icon: FileText },
  { label: 'Build Plan', description: 'Architecture plan', tab: 'Plan', icon: ListChecks },
  { label: 'Code', description: 'Generated files', tab: 'Code', icon: Code },
];

export default function VersionHistory() {
  const [panelOpen, setPanelOpen] = useState(true);
  const [versions, setVersions] = useState<VersionEntry[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null);
  const [viewport, setViewport] = useState<'desktop' | 'mobile'>('desktop');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const projectId = Number(sessionStorage.getItem('archon_project_id'));

  const load = async () => {
    if (!projectId) return;
    try {
      const data = await fetchVersions(projectId);
      const mapped: VersionEntry[] = (data.versions || []).map((e: any) => ({
        id: e.id,
        version: e.version,
        prompt: extractPrompt(e.prompt_history),
        timestamp: formatTimestamp(e.created_at),
        status: mapStatus(e.status),
      }));
      setVersions(mapped);
      if (mapped.length > 0 && selectedVersion === null) {
        setSelectedVersion(mapped[0].id);
      }
    } catch (e) {
      console.error('Failed to fetch versions:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const selected = versions.find((v) => v.id === selectedVersion);

  const handleRestore = async (executionId: number) => {
    try {
      await restoreVersion(executionId);
      await load();
    } catch (e) {
      console.error('Failed to restore version:', e);
    }
  };

  const previewUrl = selected
    ? `${API_BASE}/api/preview/${projectId}/${selected.version}`
    : '';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

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

        {selected && (
          <div className="max-w-2xl">
            {/* Version Header */}
            <div className="flex items-center gap-3 mb-5">
              <span className="rounded bg-primary/10 px-2 py-0.5 text-[11px] font-semibold font-mono text-primary uppercase tracking-wider">
                Version V{selected.version}
              </span>
              <span className="text-[11px] text-muted-foreground">{selected.timestamp}</span>
              <div className="ml-auto flex items-center gap-2">
                {versions.length > 0 && selected.id !== versions[0].id && (
                  <button
                    onClick={() => handleRestore(selected.id)}
                    className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-[11px] font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                  >
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
                      <iframe src={previewUrl} className="w-full h-[600px] border-0" title="preview" />
                    ) : (
                      <div className="w-[375px] max-h-[calc(100%-3rem)] aspect-[9/19.5] rounded-[1.5rem] border-[3px] border-border bg-background shadow-lg overflow-hidden my-6">
                        <iframe src={previewUrl} width="375" height="667" className="border-0" title="preview" />
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Validation Banner */}
              <div className="rounded border border-border bg-card px-4 py-3 flex items-start gap-2">
                <Info className="h-3.5 w-3.5 text-muted-foreground mt-0.5 flex-shrink-0" />
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Version V{selected.version} — {selected.status === 'completed' ? 'Build succeeded' : selected.status === 'failed' ? 'Build failed' : 'Build in progress'}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
