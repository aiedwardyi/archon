import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, LogOut } from 'lucide-react';
import { AuthUser } from '../services/auth';

interface SessionMenuProps {
  hasSession: boolean;
  user: AuthUser | null;
  signInHref: string;
  onNavigate: (href: string) => void;
  onSignOut: () => Promise<void> | void;
}

function getInitials(user: AuthUser | null) {
  const source = (user?.name || user?.email || 'A').trim();
  const parts = source.split(/\s+/).filter(Boolean);

  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase();
  }

  return parts
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase();
}

const SessionMenu: React.FC<SessionMenuProps> = ({ hasSession, user, signInHref, onNavigate, onSignOut }) => {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const initials = useMemo(() => getInitials(user), [user]);

  useEffect(() => {
    const handleDocumentClick = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener('click', handleDocumentClick);
    return () => document.removeEventListener('click', handleDocumentClick);
  }, []);

  const handleSignOutClick = () => {
    setOpen(false);
    void onSignOut();
  };

  if (!hasSession) {
    return (
      <button
        type="button"
        onClick={() => onNavigate(signInHref)}
        className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-white/80 backdrop-blur-xl transition hover:bg-white/[0.08] hover:text-white"
      >
        Sign In
      </button>
    );
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className="inline-flex items-center gap-3 rounded-full border border-slate-200 bg-white/90 px-2.5 py-2 text-left shadow-sm transition hover:border-slate-300 hover:bg-white"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-950 text-xs font-semibold text-white">
          {initials}
        </span>
        <span className="hidden min-w-0 sm:block">
          <span className="block truncate text-sm font-medium text-slate-900">{user?.name || 'Account'}</span>
          <span className="block truncate text-xs text-slate-500">{user?.email || ''}</span>
        </span>
        <ChevronDown size={16} className={`text-slate-400 transition ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-60 overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white p-2 shadow-[0_24px_60px_rgba(15,23,42,0.16)]">
          <div className="rounded-[1.125rem] bg-slate-50 px-4 py-3">
            <div className="text-sm font-medium text-slate-900">{user?.name || 'Account'}</div>
            <div className="mt-1 text-xs text-slate-500">{user?.email || ''}</div>
          </div>
          <button
            type="button"
            onClick={handleSignOutClick}
            className="mt-2 flex w-full items-center gap-2 rounded-[1.125rem] px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:text-slate-950"
            role="menuitem"
          >
            <LogOut size={16} />
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
};

export default SessionMenu;
