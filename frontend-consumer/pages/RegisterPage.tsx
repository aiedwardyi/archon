import React, { useMemo, useState } from 'react';
import { ArrowLeft, Sparkles } from 'lucide-react';
import GoogleAuthButton from '../components/GoogleAuthButton';
import { AuthUser, loginWithGoogle, registerWithPassword } from '../services/auth';

interface RegisterPageProps {
  onAuthSuccess: (user: AuthUser) => void;
  onNavigate: (href: string) => void;
}

function getGuestProjectId() {
  return new URLSearchParams(window.location.search).get('guest_project_id');
}

const RegisterPage: React.FC<RegisterPageProps> = ({ onAuthSuccess, onNavigate }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const guestProjectId = getGuestProjectId();

  const loginHref = useMemo(() => {
    if (!guestProjectId) return '/login';
    return `/login?guest_project_id=${encodeURIComponent(guestProjectId)}`;
  }, [guestProjectId]);

  const finish = (user: AuthUser) => {
    onAuthSuccess(user);
    onNavigate('/projects');
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const user = await registerWithPassword({
        name,
        email,
        password,
        guestProjectId,
      });
      finish(user);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Account creation failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogle = async (credential: string) => {
    setError(null);
    setIsSubmitting(true);

    try {
      const user = await loginWithGoogle(credential, guestProjectId);
      finish(user);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Google sign-in failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen overflow-y-auto bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.98),_rgba(244,247,255,0.95)_42%,_rgba(236,242,255,0.88)_100%)] px-4 py-6 text-slate-900 sm:px-6 lg:px-10">
      <div className="relative mx-auto grid min-h-[calc(100vh-3rem)] w-full max-w-6xl gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="pointer-events-none absolute inset-0 -z-10 rounded-[2.5rem] bg-[linear-gradient(to_right,rgba(15,23,42,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(15,23,42,0.04)_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:linear-gradient(to_bottom,black_35%,transparent_100%)]" />

        <section className="relative overflow-hidden rounded-[2.5rem] border border-white/80 bg-white/75 p-6 shadow-[0_30px_80px_rgba(15,23,42,0.08)] backdrop-blur sm:p-8 lg:p-10">
          <div className="flex items-center justify-between gap-4">
            <button
              type="button"
              onClick={() => onNavigate('/')}
              className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/90 px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-300 hover:bg-white"
            >
              <ArrowLeft size={16} />
              Back
            </button>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/85 px-4 py-2 text-xs font-medium uppercase tracking-[0.24em] text-slate-500 shadow-sm">
              <Sparkles size={14} />
              Consumer
            </div>
          </div>

          <div className="mt-12 max-w-xl">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg shadow-slate-950/10">
              <Sparkles size={18} />
            </div>
            <h1 className="mt-8 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
              Create your account.
            </h1>
            <p className="mt-4 max-w-lg text-base leading-7 text-slate-600 sm:text-lg">
              Keep the app you just made, unlock saved history, and return whenever you want to keep improving it.
            </p>
          </div>

          <div className="mt-12 grid gap-4 sm:grid-cols-3">
            {[
              'Save the app that is already ready to review.',
              'Keep future iterations tied to one account.',
              'Come back later without starting from scratch.',
            ].map((item) => (
              <div key={item} className="rounded-[1.75rem] border border-slate-200 bg-slate-50/85 p-5 shadow-sm">
                <div className="text-sm font-medium leading-6 text-slate-700">{item}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="flex items-center">
          <div className="w-full rounded-[2.5rem] border border-white/80 bg-white/90 p-6 shadow-[0_30px_80px_rgba(15,23,42,0.12)] backdrop-blur sm:p-8 lg:p-10">
            <div className="text-sm font-medium uppercase tracking-[0.22em] text-slate-400">Free account</div>
            <h2 className="mt-4 text-3xl font-semibold tracking-tight text-slate-950">Create your account</h2>
            <p className="mt-3 text-sm leading-6 text-slate-500">
              Start with email or Google. You can still explore the current build before you decide.
            </p>

            {guestProjectId && (
              <div className="mt-5 rounded-[1.5rem] border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                We will save your current app to this new account automatically.
              </div>
            )}

            <div className="mt-6">
              <GoogleAuthButton text="signup_with" onCredential={handleGoogle} onError={(message) => setError(message)} />
            </div>

            <div className="my-6 flex items-center gap-3">
              <div className="h-px flex-1 bg-slate-200" />
              <span className="text-xs font-medium uppercase tracking-[0.22em] text-slate-400">Or</span>
              <div className="h-px flex-1 bg-slate-200" />
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="register-name" className="mb-2 block text-sm font-medium text-slate-700">
                  Name
                </label>
                <input
                  id="register-name"
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="What should we call you?"
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-300 focus:bg-white"
                />
              </div>

              <div>
                <label htmlFor="register-email" className="mb-2 block text-sm font-medium text-slate-700">
                  Email
                </label>
                <input
                  id="register-email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-300 focus:bg-white"
                />
              </div>

              <div>
                <label htmlFor="register-password" className="mb-2 block text-sm font-medium text-slate-700">
                  Password
                </label>
                <input
                  id="register-password"
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="At least 6 characters"
                  minLength={6}
                  required
                  className="w-full rounded-[1.25rem] border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-300 focus:bg-white"
                />
              </div>

              {error && (
                <div className="rounded-[1.25rem] border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex w-full items-center justify-center rounded-[1.25rem] bg-slate-950 px-4 py-3 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSubmitting ? 'Creating your account...' : 'Create account'}
              </button>
            </form>

            <p className="mt-6 text-sm text-slate-500">
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => onNavigate(loginHref)}
                className="font-medium text-slate-950 underline decoration-slate-300 underline-offset-4 transition hover:decoration-slate-950"
              >
                Sign in
              </button>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default RegisterPage;
