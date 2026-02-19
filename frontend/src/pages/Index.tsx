import { Plus, Search, Filter, Download } from 'lucide-react';
import { projects } from '@/data/mockData';
import StatusBadge from '@/components/StatusBadge';
import { Link } from 'react-router-dom';

export default function ProjectDashboard() {
  return (
    <div className="px-6 py-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-base font-semibold text-foreground">Projects</h1>
          <p className="text-xs text-muted-foreground mt-0.5">{projects.length} projects across your workspace</p>
        </div>
        <button className="inline-flex items-center gap-1.5 rounded bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 transition-colors">
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
              <tr key={project.id} className="hover:bg-secondary/20 transition-colors cursor-pointer group">
                <td className="px-3 py-2.5">
                  <Link to="/pipeline" className="block">
                    <span className="text-xs font-medium text-foreground group-hover:text-primary transition-colors">{project.name}</span>
                    <span className="block text-[11px] text-muted-foreground mt-0.5">{project.description}</span>
                  </Link>
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
