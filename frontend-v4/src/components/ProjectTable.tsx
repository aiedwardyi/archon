import { useState, useCallback } from "react";
import { MoreHorizontal, FolderOpen, Download, ChevronUp, ChevronDown, ArrowUpDown } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";
import { DeleteProjectModal } from "@/components/DeleteProjectModal";

const STORAGE_KEY = "archon_selected_projects";

type ProjectStatus = "Running" | "Completed" | "Failed" | "Idle";

interface Project {
  name: string;
  description: string;
  id: number;
  status: ProjectStatus;
  lastRun: string;
  versions: string;
  created: string;
}

interface ProjectTableProps {
  projects: Project[];
  onProjectSelect?: (id: number) => void;
}

type SortKey = "name" | "id" | "status" | "lastRun" | "versions" | "created";
type SortDir = "asc" | "desc";

const statusOrder: Record<ProjectStatus, number> = { Running: 0, Completed: 1, Failed: 2, Idle: 3 };

const statusStyles: Record<ProjectStatus, { dot: string; text: string; bg: string }> = {
  Running: { dot: "bg-blue-500", text: "text-blue-600 dark:text-blue-400", bg: "bg-blue-50 dark:bg-blue-500/10" },
  Completed: { dot: "bg-emerald-500", text: "text-emerald-600 dark:text-emerald-400", bg: "bg-emerald-50 dark:bg-emerald-500/10" },
  Failed: { dot: "bg-destructive", text: "text-destructive", bg: "bg-red-50 dark:bg-red-500/10" },
  Idle: { dot: "bg-gray-400", text: "text-gray-500 dark:text-gray-400", bg: "bg-gray-50 dark:bg-gray-500/10" },
};

export const ProjectTable = ({ projects, onProjectSelect }: ProjectTableProps) => {
  const [selected, setSelected] = useState<Set<number>>(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      return stored ? new Set(JSON.parse(stored) as number[]) : new Set();
    } catch { return new Set(); }
  });
  const [sortKey, setSortKey] = useState<SortKey>("id");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const { t } = useLanguage();

  const persistSelected = useCallback((next: Set<number>) => {
    setSelected(next);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...next]));
  }, []);

  const columns: { key: SortKey; label: string; sortable: boolean }[] = [
    { key: "name", label: t("project"), sortable: true },
    { key: "id", label: t("id"), sortable: true },
    { key: "status", label: t("status"), sortable: true },
    { key: "lastRun", label: t("lastRun"), sortable: true },
    { key: "versions", label: t("versions"), sortable: false },
    { key: "created", label: t("created"), sortable: true },
  ];

  const allSelected = selected.size === projects.length && projects.length > 0;
  const someSelected = selected.size > 0 && !allSelected;

  const toggleAll = () => {
    if (allSelected) persistSelected(new Set());
    else persistSelected(new Set(projects.map((p) => p.id)));
  };

  const toggle = (id: number) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    persistSelected(next);
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("asc"); }
  };

  const sorted = [...projects].sort((a, b) => {
    const dir = sortDir === "asc" ? 1 : -1;
    if (sortKey === "name") return dir * a.name.localeCompare(b.name);
    if (sortKey === "id") return dir * (a.id - b.id);
    if (sortKey === "status") return dir * (statusOrder[a.status] - statusOrder[b.status]);
    if (sortKey === "lastRun" || sortKey === "created") return dir * (new Date(a[sortKey]).getTime() - new Date(b[sortKey]).getTime());
    return 0;
  });

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <ArrowUpDown className="h-3 w-3 opacity-0 group-hover:opacity-40 transition-opacity" />;
    return sortDir === "asc" ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />;
  };

  return (
    <div className="border border-border rounded-md overflow-hidden bg-card">
      {/* Bulk Actions Bar */}
      {selected.size > 0 && (
        <div className="px-4 py-2 bg-primary/5 border-b border-border flex items-center justify-between">
          <span className="text-xs font-medium text-foreground">{selected.size} {t("selected")}</span>
          <div className="flex items-center gap-2">
            <button className="text-xs font-medium text-muted-foreground hover:text-foreground px-2 py-1 rounded hover:bg-secondary transition-colors">
              {t("export_")}
            </button>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="text-xs font-medium text-destructive hover:text-destructive/80 px-2 py-1 rounded hover:bg-destructive/5 transition-colors"
            >
              {t("delete_")}
            </button>
          </div>
        </div>
      )}

      {/* Table Header */}
      <div className="grid grid-cols-[40px_1fr_70px_110px_120px_80px_110px_80px] px-2 py-2.5 border-b border-border bg-secondary/60">
        <div className="flex items-center justify-center">
          <input
            type="checkbox"
            checked={allSelected}
            ref={(el) => { if (el) el.indeterminate = someSelected; }}
            onChange={toggleAll}
            className="h-3.5 w-3.5 rounded border-border accent-primary cursor-pointer"
          />
        </div>
        {columns.map((col) => (
          <button
            key={col.key}
            onClick={() => col.sortable && handleSort(col.key)}
            className={`group flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground ${col.sortable ? "cursor-pointer hover:text-foreground" : "cursor-default"} transition-colors text-left`}
          >
            {col.label}
            {col.sortable && <SortIcon col={col.key} />}
          </button>
        ))}
        <div />
      </div>

      {/* Table Rows */}
      <div className="divide-y divide-border">
        {sorted.map((p) => {
          const isSelected = selected.has(p.id);
          const style = statusStyles[p.status];
          return (
            <div
              key={p.id}
              onClick={() => onProjectSelect?.(p.id)}
              className={`grid grid-cols-[40px_1fr_70px_110px_120px_80px_110px_80px] px-2 items-center transition-colors ${
                isSelected ? "bg-primary/5" : "hover:bg-secondary/40"
              }`}
            >
              <div
                className="flex items-center justify-center h-full cursor-default py-2.5"
                onClick={(e) => { e.stopPropagation(); toggle(p.id); }}
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => {}}
                  className="h-3.5 w-3.5 rounded border-border accent-primary cursor-pointer pointer-events-none"
                />
              </div>

              <div className="flex items-center gap-2.5 min-w-0 cursor-pointer py-2.5">
                <div className="h-8 w-8 rounded-md bg-secondary flex items-center justify-center flex-shrink-0">
                  <FolderOpen className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-medium text-foreground truncate leading-tight">{p.name}</div>
                  <div className="text-[11px] text-muted-foreground truncate leading-tight mt-0.5">{p.description}</div>
                </div>
              </div>

              <div className="text-xs text-muted-foreground font-mono cursor-pointer py-2.5">#{p.id}</div>

              <div className="cursor-pointer py-2.5">
                <span className={`inline-flex items-center gap-1.5 text-[11px] font-medium px-2 py-0.5 rounded-full ${style.text} ${style.bg}`}>
                  <span className={`inline-block h-1.5 w-1.5 rounded-full ${style.dot} ${p.status === "Running" ? "animate-pulse" : ""}`} />
                  {p.status === "Running" ? t("running") : p.status}
                </span>
              </div>

              <div className="text-xs text-muted-foreground cursor-pointer py-2.5">{p.lastRun}</div>
              <div className="text-xs text-muted-foreground cursor-pointer py-2.5">{p.versions}</div>
              <div className="text-xs text-muted-foreground cursor-pointer py-2.5">{p.created}</div>

              <div className="flex items-center justify-end gap-1 py-2.5">
                <button className="h-7 w-7 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors" title="Download">
                  <Download className="h-3.5 w-3.5" />
                </button>
                <button className="h-7 w-7 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors" title="More">
                  <MoreHorizontal className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-border bg-secondary/30 flex items-center justify-between">
        <span className="text-[11px] text-muted-foreground">
          {t("showing")} <span className="font-medium text-foreground">{projects.length}</span> {t("of")} {projects.length} {t("projects").toLowerCase()}
        </span>
        <div className="flex items-center gap-1">
          <button className="h-7 px-2.5 text-[11px] font-medium border border-border rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors disabled:opacity-40" disabled>
            {t("previous")}
          </button>
          <button className="h-7 w-7 text-[11px] font-medium bg-primary text-primary-foreground rounded-md">
            1
          </button>
          <button className="h-7 px-2.5 text-[11px] font-medium border border-border rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors disabled:opacity-40" disabled>
            {t("next")}
          </button>
        </div>
      </div>

      <DeleteProjectModal
        open={showDeleteModal}
        projectCount={selected.size}
        projectNames={projects.filter(p => selected.has(p.id)).map(p => p.name)}
        onConfirm={async () => {
          const ids = Array.from(selected);
          await Promise.all(ids.map(id =>
            fetch(`http://localhost:5000/api/projects/${id}`, { method: "DELETE" })
          ));
          persistSelected(new Set());
          setShowDeleteModal(false);
        }}
        onClose={() => setShowDeleteModal(false)}
      />
    </div>
  );
};
