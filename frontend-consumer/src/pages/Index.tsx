import { useState, useEffect } from 'react';
import { Plus, Search, Filter, Download, Loader2 } from 'lucide-react';
import StatusBadge from '@/components/StatusBadge';
import { useNavigate } from 'react-router-dom';
import { fetchProjects, createProject } from '@/lib/api';
import type { ProjectStatus } from '@/data/mockData';

interface ProjectRow {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  lastRun: string;
  versions: number;
  created: string;
}

function mapStatus(raw: string): ProjectStatus {
  if (raw === 'success') return 'completed';
  if (raw === 'error') return 'failed';
  if (raw === 'running' || raw === 'in_progress') return 'running';
  if (raw === 'pending') return 'pending';
  if (raw === 'completed') return 'completed';
  if (raw === 'failed') return 'failed';
  return 'pending';
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function timeAgo(iso: string | null): string {
  if (!iso) return 'Never';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days > 1 ? 's' : ''} ago`;
}

export default function ProjectDashboard() {
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const load = async () => {
    try {
      const data = await fetchProjects();
      const mapped: ProjectRow[] = (data || []).map((p: any) => ({
        id: String(p.id),
        name: p.name,
        description: p.description || '',
        status: mapStatus(p.status),
        lastRun: timeAgo(p.updated_at),
        versions: p.execution_count ?? 0,
        created: formatDate(p.created_at),
      }));
      setProjects(mapped);
    } catch (e) {
      console.error('Failed to fetch projects:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleNewProject = async () => {
    const name = window.prompt('Project name:');
    if (!name) return;
    try {
      await createProject(name);
      await load();
    } catch (e) {
      console.error('Failed to create project:', e);
    }
  };

  const handleRowClick = (project: ProjectRow) => {
    sessionStorage.setItem('archon_project_id', project.id);
    sessionStorage.setItem('archon_project_name', project.name);
    navigate('/pipeline');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
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
          onClick={handleNewProject}
          className="inline-flex items-center gap-1.5 rounded bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-3.5 w-3.5" />
          New Project
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-3">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search projects..."
            className="w-full rounded border border-border bg-card pl-8 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
        <button className="inline-flex items-center gap-1 rounded border border-border bg-card px-2.5 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
          <Filter className="h-3 w-3" />
          Filter
        </button>
      </div>

      {/* Table */}
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
            {projects.map((project) => (
              <tr
                key={project.id}
                onClick={() => handleRowClick(project)}
                className="hover:bg-secondary/20 transition-colors cursor-pointer group"
              >
                <td className="px-3 py-2.5">
                  <span className="text-xs font-medium text-foreground group-hover:text-primary transition-colors">{project.name}</span>
                  <span className="block text-[11px] text-muted-foreground mt-0.5">{project.description}</span>
                </td>
                <td className="px-3 py-2.5">
                  <StatusBadge status={project.status} />
                </td>
                <td className="px-3 py-2.5 text-[11px] text-muted-foreground">{project.lastRun}</td>
                <td className="px-3 py-2.5 text-[11px] text-muted-foreground font-mono">{project.versions}</td>
                <td className="px-3 py-2.5 text-[11px] text-muted-foreground">{project.created}</td>
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
    </div>
  );
}
