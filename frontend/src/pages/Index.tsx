import { useState, useEffect } from 'react';
import { Plus, Search, Filter, Download, Loader2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { listProjects, createProject, type Project } from '@/services/api';
import StatusBadge from '@/components/StatusBadge';

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs} hour${hrs > 1 ? 's' : ''} ago`;
  const days = Math.floor(hrs / 24);
  return `${days} day${days > 1 ? 's' : ''} ago`;
}

export default function ProjectDashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadProjects();
    // Poll every 5s so Running status updates live
    const interval = setInterval(loadProjects, 5000);
    return () => clearInterval(interval);
  }, []);

  async function loadProjects() {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const project = await createProject(newName.trim(), newDesc.trim());
      setProjects((prev) => [project, ...prev]);
      setShowNew(false);
      setNewName('');
      setNewDesc('');
      // Navigate straight to the pipeline for the new project
      navigate(`/pipeline?project=${project.id}`);
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  }

  const filtered = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.description.toLowerCase().includes(search.toLowerCase())
  );

  // Map backend status to display status
  function displayStatus(status: string): 'running' | 'completed' | 'failed' | 'pending' {
    if (status === 'in_progress') return 'running';
    if (status === 'completed') return 'completed';
    if (status === 'failed') return 'failed';
    return 'pending';
  }

  return (
    <div className="px-6 py-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-base font-semibold text-foreground">Projects</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{projects.length} projects across your workspace</p>
        </div>
        <button
          onClick={() => setShowNew(true)}
          className="inline-flex items-center gap-1.5 rounded bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          New Project
        </button>
      </div>

      {/* New project form */}
      {showNew && (
        <div className="mb-4 rounded border border-border bg-card p-4 max-w-lg">
          <p className="text-xs font-semibold text-foreground mb-3">New Project</p>
          <input
            autoFocus
            type="text"
            placeholder="Project name (e.g. checkout-service)"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            className="w-full rounded border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring mb-2"
          />
          <input
            type="text"
            placeholder="Description (e.g. Payment checkout microservice)"
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            className="w-full rounded border border-border bg-background px-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring mb-3"
          />
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              disabled={creating || !newName.trim()}
              className="inline-flex items-center gap-1.5 rounded bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {creating && <Loader2 className="h-3 w-3 animate-spin" />}
              Create & Run
            </button>
            <button
              onClick={() => { setShowNew(false); setNewName(''); setNewDesc(''); }}
              className="rounded border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2 mb-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search projects..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded border border-border bg-card pl-8 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
        <button className="inline-flex items-center gap-1 rounded border border-border bg-card px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
          <Filter className="h-3 w-3" />
          Filter
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin mr-2" />
          <span className="text-xs">Loading projects...</span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p className="text-xs">{search ? 'No projects match your search.' : 'No projects yet. Create your first one!'}</p>
        </div>
      ) : (
        <div className="rounded border border-border bg-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-secondary/30">
                <th className="text-left px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Project</th>
                <th className="text-left px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Status</th>
                <th className="text-left px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Last Run</th>
                <th className="text-left px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Versions</th>
                <th className="text-left px-3 py-2 text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Created</th>
                <th className="w-10 px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((project) => (
                <tr key={project.id} className="hover:bg-secondary/20 transition-colors cursor-pointer group">
                  <td className="px-3 py-2.5">
                    <Link to={`/pipeline?project=${project.id}`} className="block">
                      <span className="text-xs font-medium text-foreground group-hover:text-primary transition-colors">{project.name}</span>
                      <span className="block text-[11px] text-muted-foreground mt-0.5">{project.description}</span>
                    </Link>
                  </td>
                  <td className="px-3 py-2.5">
                    <StatusBadge status={displayStatus(project.status)} />
                  </td>
                  <td className="px-3 py-2.5 text-[11px] text-muted-foreground">{timeAgo(project.updated_at)}</td>
                  <td className="px-3 py-2.5 text-[11px] text-muted-foreground font-mono">{project.execution_count}</td>
                  <td className="px-3 py-2.5 text-[11px] text-muted-foreground">{formatDate(project.created_at)}</td>
                  <td className="px-3 py-2.5">
                    <button className="rounded p-1 text-muted-foreground/0 group-hover:text-muted-foreground hover:!text-foreground hover:bg-secondary transition-colors" title="Download Report">
                      <Download className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
