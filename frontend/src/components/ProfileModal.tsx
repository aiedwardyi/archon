import { useEffect, useState } from "react";
import { X, User, Mail, Calendar, CreditCard } from "lucide-react";
import { useLanguage } from "@/contexts/LanguageContext";

interface ProfileModalProps {
  open: boolean;
  onClose: () => void;
}

export const ProfileModal = ({ open, onClose }: ProfileModalProps) => {
  const { t } = useLanguage();
  const [userName, setUserName] = useState("there");
  const [userEmail, setUserEmail] = useState("...");
  const [userCreatedAt, setUserCreatedAt] = useState<string | null>(null);

  useEffect(() => {
    const getDisplayName = (name?: string, email?: string) => {
      const trimmedName = (name || "").trim();
      if (trimmedName) return trimmedName;
      const emailPrefix = (email || "").split("@")[0]?.trim();
      return emailPrefix || "there";
    };

    const loadUser = async () => {
      const cached = localStorage.getItem("archon_user");
      if (cached) {
        try {
          const u = JSON.parse(cached);
          const email = u?.email || "...";
          setUserEmail(email);
          setUserName(getDisplayName(u?.name, email));
          setUserCreatedAt(u?.created_at || null);
        } catch {}
      }

      const params = new URLSearchParams(window.location.search);
      const urlToken = params.get("token");
      const token = localStorage.getItem("archon_token") || urlToken;
      if (!token) return;

      try {
        const res = await fetch("http://localhost:5000/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const d = await res.json();
        const email = d?.email || "...";
        setUserEmail(email);
        setUserName(getDisplayName(d?.name, email));
        if (d?.created_at) setUserCreatedAt(d.created_at);
      } catch {}
    };

    loadUser();
    window.addEventListener("storage", loadUser);
    return () => window.removeEventListener("storage", loadUser);
  }, []);

  const initials = (() => {
    const trimmedName = userName.trim();
    if (trimmedName && trimmedName !== "there") {
      const parts = trimmedName.split(/\s+/).filter(Boolean);
      const first = parts[0]?.[0] || "";
      const second = parts[1]?.[0] || parts[0]?.[1] || "";
      return (first + second).toUpperCase() || "TH";
    }
    const emailPrefix = userEmail.split("@")[0] || "TH";
    return emailPrefix.slice(0, 2).toUpperCase();
  })();

  const memberSince = userCreatedAt
    ? new Date(userCreatedAt).toLocaleDateString("en-US", { month: "long", year: "numeric" })
    : "—";

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      <div className="absolute inset-0 bg-background/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-card border border-border rounded-md shadow-lg w-full max-w-md z-10 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <h2 className="text-xs font-semibold text-foreground uppercase tracking-wider">{t("profile")}</h2>
          <button onClick={onClose} className="h-6 w-6 flex items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="px-5 py-4 border-b border-border flex items-center gap-3">
          <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold flex-shrink-0">
            {initials}
          </div>
          <div>
            <div className="text-sm font-semibold text-foreground">{userName}</div>
            <div className="text-[11px] text-muted-foreground">{userEmail}</div>
          </div>
        </div>

        <div className="divide-y divide-border">
          {[
            { icon: User, label: t("fullName"), value: userName },
            { icon: Mail, label: t("email"), value: userEmail },
            { icon: CreditCard, label: t("plan"), value: t("free") },
            { icon: Calendar, label: t("memberSince"), value: memberSince },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="px-5 py-3 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">{label}</span>
              </div>
              <span className="text-xs font-medium text-foreground">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
