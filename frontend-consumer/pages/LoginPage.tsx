import React, { useMemo, useState } from 'react';
import { ArrowLeft, Sparkles } from 'lucide-react';
import GoogleAuthButton from '../components/GoogleAuthButton';
import { AuthUser, claimGuestProject, loginWithGoogle, loginWithPassword } from '../services/auth';

interface LoginPageProps {
  onAuthSuccess: (user: AuthUser) => void;
  onNavigate: (href: string) => void;
}

function getGuestProjectId() {
  return new URLSearchParams(window.location.search).get('guest_project_id');
}

const LoginPage: React.FC<LoginPageProps> = ({ onAuthSuccess, onNavigate }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const guestProjectId = getGuestProjectId();

  const registerHref = useMemo(() => {
    if (!guestProjectId) return '/register';
    return `/register?guest_project_id=${encodeURIComponent(guestProjectId)}`;
  }, [guestProjectId]);

  const finishSignIn = async (user: AuthUser) => {
    if (guestProjectId) {
      try {
        await claimGuestProject(guestProjectId);
      } catch {
        // Existing users should still be able to continue even if the guest project is no longer claimable.
      }
    }

    onAuthSuccess(user);
    onNavigate('/projects');
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const user = await loginWithPassword(email, password);
      await finishSignIn(user);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Sign in failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogle = async (credential: string) => {
    setError(null);
    setIsSubmitting(true);

    try {
      const user = await loginWithGoogle(credential);
      await finishSignIn(user);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Google sign-in failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-y-auto bg-[#03050f] px-4 py-16 text-white sm:px-6">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute left-[-12%] top-[-8%] h-[38rem] w-[38rem] rounded-full blur-[110px]"
          style={{ backgroundColor: 'rgba(79, 70, 229, 0.42)', animation: 'orbFloatA 18s ease-in-out infinite' }}
        />
        <div
          className="absolute right-[-10%] top-[10%] h-[34rem] w-[34rem] rounded-full blur-[110px]"
          style={{ backgroundColor: 'rgba(124, 58, 237, 0.34)', animation: 'orbFloatB 20s ease-in-out infinite' }}
        />
        <div
          className="absolute bottom-[-16%] left-[28%] h-[32rem] w-[32rem] rounded-full blur-[110px]"
          style={{ backgroundColor: 'rgba(8, 145, 178, 0.28)', animation: 'orbFloatC 16s ease-in-out infinite' }}
        />
      </div>

      <style>{`
        @keyframes orbFloatA {
          0% { transform: translate3d(-8%, -2%, 0) scale(1); }
          50% { transform: translate3d(6%, 5%, 0) scale(1.12); }
          100% { transform: translate3d(-8%, -2%, 0) scale(1); }
        }
        @keyframes orbFloatB {
          0% { transform: translate3d(4%, 3%, 0) scale(1.05); }
          50% { transform: translate3d(-6%, -5%, 0) scale(0.96); }
          100% { transform: translate3d(4%, 3%, 0) scale(1.05); }
        }
        @keyframes orbFloatC {
          0% { transform: translate3d(0, 0, 0) scale(1); }
          50% { transform: translate3d(-5%, 6%, 0) scale(1.1); }
          100% { transform: translate3d(0, 0, 0) scale(1); }
        }
      `}</style>

      <button
        type="button"
        onClick={() => onNavigate('/')}
        className="absolute left-4 top-4 z-10 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.05] px-4 py-2 text-sm font-medium text-white/78 backdrop-blur-xl transition hover:bg-white/[0.08] hover:text-white sm:left-6 sm:top-6"
      >
        <ArrowLeft size={16} />
        Back
      </button>

      <div className="relative z-10 w-full max-w-md">
        <div className="w-full rounded-[2rem] border border-white/10 bg-[#07101f] p-8 shadow-[0_30px_80px_rgba(2,6,23,0.55)] backdrop-blur-2xl">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-[1.3rem] border border-white/10 bg-white/[0.05] text-indigo-200">
              <Sparkles size={18} />
            </div>
            <div>
              <div className="text-sm font-semibold tracking-[0.24em] text-white">ARCHON</div>
              <div className="text-xs uppercase tracking-[0.22em] text-white/40">Consumer Studio</div>
            </div>
          </div>

          <h1 className="mt-8 text-3xl font-semibold tracking-tight text-white">Sign in and keep building</h1>
          <p className="mt-3 text-sm leading-6 text-white/56">
            Use your email or Google account. If you just built something as a guest, we will attach it after you sign in.
          </p>

          {guestProjectId && (
            <div className="mt-5 rounded-[1.2rem] border border-emerald-400/20 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
              Your current app will be connected after you sign in.
            </div>
          )}

          <div className="mt-6 rounded-[1.2rem] border border-white/10 bg-white/[0.05] p-1.5">
            <GoogleAuthButton text="signin_with" onCredential={handleGoogle} onError={(message) => setError(message)} />
          </div>

          <div className="my-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-white/10" />
            <span className="text-xs font-medium uppercase tracking-[0.22em] text-white/34">Or</span>
            <div className="h-px flex-1 bg-white/10" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="login-email" className="mb-2 block text-sm font-medium text-white/72">
                Email
              </label>
              <input
                id="login-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
                className="w-full rounded-[1.2rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-indigo-400/40 focus:bg-white/[0.06]"
              />
            </div>

            <div>
              <label htmlFor="login-password" className="mb-2 block text-sm font-medium text-white/72">
                Password
              </label>
              <input
                id="login-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                required
                className="w-full rounded-[1.2rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-indigo-400/40 focus:bg-white/[0.06]"
              />
            </div>

            {error && (
              <div className="rounded-[1.2rem] border border-rose-400/20 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex w-full items-center justify-center rounded-[1.2rem] bg-[linear-gradient(135deg,#4f46e5,#7c3aed)] px-4 py-3 text-sm font-medium text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="mt-6 text-sm text-white/56">
            Need an account?{' '}
            <button
              type="button"
              onClick={() => onNavigate(registerHref)}
              className="font-medium text-indigo-300 transition hover:text-indigo-200"
            >
              Create one
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
