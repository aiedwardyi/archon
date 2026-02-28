import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface DeleteProjectModalProps {
  open: boolean;
  projectCount: number;
  projectNames: string[];
  onConfirm: () => Promise<void>;
  onClose: () => void;
}

export const DeleteProjectModal = ({ open, projectCount, projectNames, onConfirm, onClose }: DeleteProjectModalProps) => {
  const { t } = useLanguage();
  const [confirmText, setConfirmText] = useState("");
  const [deleting, setDeleting] = useState(false);

  if (!open) return null;

  const canConfirm = confirmText === "DELETE";

  const handleConfirm = async () => {
    if (!canConfirm) return;
    setDeleting(true);
    try {
      await onConfirm();
    } finally {
      setDeleting(false);
      setConfirmText("");
    }
  };

  const handleClose = () => {
    setConfirmText("");
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm bg-black/50"
      onClick={handleClose}
    >
      <div
        className="w-full max-w-md border border-border rounded-md bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-5 py-4 border-b border-border flex items-center gap-3">
          <div className="h-8 w-8 rounded-md bg-destructive/10 flex items-center justify-center flex-shrink-0">
            <AlertTriangle className="h-4 w-4 text-destructive" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">{t("deleteNProjects").replace("{n}", String(projectCount))}{projectCount !== 1 ? "s" : ""}</h2>
            <p className="text-[11px] text-muted-foreground mt-0.5">{t("deleteCannotUndo")}</p>
          </div>
        </div>

        <div className="px-5 py-4 space-y-3">
          <div className="text-xs text-muted-foreground">
            {t("deleteListWarning")}
          </div>
          <div className="border border-border rounded-md bg-secondary/30 p-3 max-h-32 overflow-y-auto space-y-1">
            {projectNames.map((name, i) => (
              <div key={i} className="text-xs text-foreground font-medium">{name}</div>
            ))}
          </div>
          <div className="text-xs text-muted-foreground">
            {t("typeDeleteToConfirm")}
          </div>
          <input
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="DELETE"
            autoFocus
            className="w-full h-8 px-3 text-sm border border-border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-destructive"
          />
        </div>

        <div className="px-5 py-3 border-t border-border flex items-center justify-end gap-2">
          <button
            onClick={handleClose}
            className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors"
          >
            {t("cancel")}
          </button>
          <button
            onClick={handleConfirm}
            disabled={!canConfirm || deleting}
            className="h-8 px-3 text-xs font-semibold rounded-md transition-colors bg-destructive text-destructive-foreground hover:bg-destructive/90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {deleting ? "Deleting..." : t("delete_")}
          </button>
        </div>
      </div>
    </div>
  );
};
