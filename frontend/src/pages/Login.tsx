import { useState } from "react";
import { authService } from "@/lib/auth";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authService.login(email, password);
      if (!localStorage.getItem("theme")) {
        localStorage.setItem("theme", "dark");
      }
      localStorage.setItem("archon_active_tab", "projects");
      window.location.href = "/?tab=projects";
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-[#0A0A0A] z-50 flex">
      {/* Left side — Auth form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="flex items-center gap-2.5 mb-10">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <polygon
                points="12,2 20.66,7 20.66,17 12,22 3.34,17 3.34,7"
                fill="none"
                stroke="#3b82f6"
                strokeWidth="2"
                strokeLinejoin="round"
              />
            </svg>
            <span className="text-xl font-bold tracking-tight text-white">
              Archon
            </span>
          </div>

          <div className="bg-[#111111] border border-[#1F1F1F] rounded-xl py-10 px-8">
            <h1 className="text-2xl font-semibold text-white mb-1">
              Welcome back
            </h1>
            <p className="text-sm text-zinc-400 mb-8">
              Sign in to your Archon account
            </p>

            {/* Google button */}
            <button
              type="button"
              className="w-full flex items-center justify-center gap-3 px-4 py-2.5 bg-[#1A1A1A] border border-[#2A2A2A] rounded-lg text-sm font-medium text-white hover:bg-[#222222] transition-colors"
            >
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A11.96 11.96 0 001 12c0 1.94.46 3.77 1.18 5.07l3.66-2.98z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Continue with Google
            </button>

            {/* Divider */}
            <div className="flex items-center gap-3 my-6">
              <div className="flex-1 h-px bg-[#2A2A2A]" />
              <span className="text-xs text-zinc-500 uppercase tracking-wider">
                or
              </span>
              <div className="flex-1 h-px bg-[#2A2A2A]" />
            </div>

            {/* Email/password form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-zinc-300 mb-1.5 block">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className="w-full px-3 py-2.5 text-sm bg-[#1A1A1A] border border-[#2A2A2A] rounded-lg text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500/50 transition-colors"
                />
              </div>
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-sm font-medium text-zinc-300">Password</label>
                  <a href="/forgot-password" className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors">
                    Forgot password?
                  </a>
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full px-3 py-2.5 text-sm bg-[#1A1A1A] border border-[#2A2A2A] rounded-lg text-white placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500/50 transition-colors"
                />
              </div>

              {error && (
                <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 bg-white text-black text-sm font-semibold rounded-lg hover:bg-zinc-100 disabled:opacity-50 transition-colors"
              >
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </form>

            <p className="text-sm text-center text-zinc-500 mt-6">
              Don't have an account?{" "}
              <a
                href="/register"
                className="text-white hover:underline font-medium"
              >
                Sign up
              </a>
            </p>
          </div>
        </div>
      </div>

      {/* Right side — Value props */}
      <div className="hidden lg:flex flex-col w-1/2 bg-gradient-to-br from-[#0D1117] via-[#0F172A] to-[#1E1B4B] border-l border-[#1E293B] p-16 relative">
        <div className="flex flex-col justify-center flex-1">
          <div className="max-w-lg">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 mb-8">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              <span className="text-xs font-semibold tracking-widest text-blue-400 uppercase">Why agencies choose Archon</span>
            </div>
            <h1 className="text-5xl font-extrabold text-white leading-[1.15] tracking-tight mb-10">
              Build client software.<br />Prove every decision.
            </h1>
            <ul className="space-y-5">
              {[
                "Deliver client apps in hours, not weeks",
                "Every build is IBM Watson-certified for quality",
                "Show clients exactly what was built and why",
                "One-click sign-off reports for every client",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3">
                  <svg
                    className="w-5 h-5 text-blue-400 mt-0.5 shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span className="text-zinc-200 text-base leading-snug">{item}</span>
                </li>
              ))}
            </ul>
            <div className="mt-10 flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 border border-white/10 w-fit">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L3 7V12C3 16.55 6.84 20.74 12 22C17.16 20.74 21 16.55 21 12V7L12 2Z"
                  fill="none" stroke="#6366f1" strokeWidth="2" strokeLinejoin="round"/>
              </svg>
              <span className="text-zinc-300 text-xs font-medium">Enterprise AI Governance — Powered by IBM Watson</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
