import type { ProjectStatus } from '@/data/mockData';

const statusConfig: Record<ProjectStatus, { label: string; dotClass: string }> = {
  running: { label: 'Running', dotClass: 'bg-status-running status-pulse' },
  completed: { label: 'Completed', dotClass: 'bg-status-complete' },
  failed: { label: 'Failed', dotClass: 'bg-status-failed' },
  pending: { label: 'Pending', dotClass: 'bg-muted-foreground' },
};

export default function StatusBadge({ status }: { status: ProjectStatus }) {
  const config = statusConfig[status];
  return (
    <span className="inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-[11px] font-medium bg-secondary text-muted-foreground">
      <span className={`h-1.5 w-1.5 rounded-full ${config.dotClass}`} />
      {config.label}
    </span>
  );
}
