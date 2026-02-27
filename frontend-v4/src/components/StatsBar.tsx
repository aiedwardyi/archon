interface ProjectStat {
  label: string;
  value: number;
  color?: string;
}

interface StatsBarProps {
  stats: ProjectStat[];
}

export const StatsBar = ({ stats }: StatsBarProps) => {
  const total = stats[0]?.value || 1;
  const segments = stats.slice(1);

  return (
    <div className="border border-border rounded-md overflow-hidden bg-card">
      <div className="grid grid-cols-4 gap-px bg-border">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-card px-4 py-3">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              {stat.label}
            </div>
            <div className={`text-2xl font-bold tracking-tight mt-0.5 ${stat.color || "text-foreground"}`}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>
      {/* Stacked distribution bar */}
      <div className="h-1.5 flex">
        {segments.map((stat) => (
          <div
            key={stat.label}
            className={`h-full transition-all ${
              stat.color?.includes("blue") ? "bg-blue-500" :
              stat.color?.includes("success") ? "bg-emerald-500" :
              stat.color?.includes("destructive") ? "bg-destructive" :
              "bg-muted-foreground"
            }`}
            style={{ width: `${(stat.value / total) * 100}%` }}
          />
        ))}
      </div>
    </div>
  );
};
