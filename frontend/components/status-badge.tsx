type StatusType = "running" | "completed" | "failed" | "pending"

const statusConfig: Record<
  StatusType,
  { label: string; dotClass: string; bgClass: string; textClass: string }
> = {
  running: {
    label: "Running",
    dotClass: "bg-info animate-pulse-dot",
    bgClass: "bg-info/10",
    textClass: "text-info",
  },
  completed: {
    label: "Completed",
    dotClass: "bg-success",
    bgClass: "bg-success/10",
    textClass: "text-success",
  },
  failed: {
    label: "Failed",
    dotClass: "bg-destructive",
    bgClass: "bg-destructive/10",
    textClass: "text-destructive",
  },
  pending: {
    label: "Pending",
    dotClass: "bg-muted-foreground",
    bgClass: "bg-muted",
    textClass: "text-muted-foreground",
  },
}

export function StatusBadge({ status }: { status: StatusType }) {
  const config = statusConfig[status]
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgClass} ${config.textClass}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dotClass}`} />
      {config.label}
    </span>
  )
}
