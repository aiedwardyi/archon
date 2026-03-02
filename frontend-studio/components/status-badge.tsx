import { useLanguage } from "@/contexts/LanguageContext"

type StatusType = "running" | "completed" | "failed" | "pending"

const statusConfig: Record<
  StatusType,
  { labelKey: "running" | "completed" | "failed" | "pending"; dotClass: string; bgClass: string; textClass: string }
> = {
  running: {
    labelKey: "running",
    dotClass: "bg-info animate-pulse-dot",
    bgClass: "bg-info/10",
    textClass: "text-info",
  },
  completed: {
    labelKey: "completed",
    dotClass: "bg-success",
    bgClass: "bg-success/10",
    textClass: "text-success",
  },
  failed: {
    labelKey: "failed",
    dotClass: "bg-destructive",
    bgClass: "bg-destructive/10",
    textClass: "text-destructive",
  },
  pending: {
    labelKey: "pending",
    dotClass: "bg-muted-foreground",
    bgClass: "bg-muted",
    textClass: "text-muted-foreground",
  },
}

export function StatusBadge({ status }: { status: StatusType }) {
  const { t } = useLanguage()
  const config = statusConfig[status]
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgClass} ${config.textClass}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dotClass}`} />
      {t(config.labelKey)}
    </span>
  )
}
