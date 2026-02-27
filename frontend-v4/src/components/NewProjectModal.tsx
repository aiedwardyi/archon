import { useState } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import { createProject } from "@/services/api";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";

interface NewProjectModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: (projectId: number) => void;
}

export const NewProjectModal = ({ open, onClose, onCreated }: NewProjectModalProps) => {
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { t } = useLanguage();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || creating) return;
    setError(null);
    setCreating(true);
    try {
      const project = await createProject(name.trim(), "");
      setName("");
      onCreated(project.id);
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  const handleClose = () => {
    if (creating) return;
    setName("");
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) handleClose(); }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("newProject")}</DialogTitle>
          <DialogDescription className="sr-only">
            {t("newProject")}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground">
              {t("projectName")} <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
              required
              className="w-full h-8 px-3 text-sm border border-border rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          {error && (
            <div className="text-xs text-destructive bg-destructive/10 border border-destructive/30 rounded-md px-3 py-2">
              {error}
            </div>
          )}
          <DialogFooter>
            <button
              type="button"
              onClick={handleClose}
              disabled={creating}
              className="h-8 px-3 text-xs font-medium border border-border rounded-md text-foreground hover:bg-secondary transition-colors disabled:opacity-40"
            >
              {t("cancel")}
            </button>
            <button
              type="submit"
              disabled={!name.trim() || creating}
              className="h-8 px-3 text-xs font-semibold rounded-md bg-primary text-primary-foreground hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
            >
              {creating && <Loader2 className="h-3 w-3 animate-spin" />}
              {creating ? t("creating") : t("create")}
            </button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
