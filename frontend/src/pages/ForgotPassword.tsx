import { useState } from "react";
import { authService } from "@/lib/auth";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authService.forgotPassword(email);
      setSent(true);
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
            {sent ? (
              <div className="text-center">
                <div className="text-4xl mb-4">📧</div>
                <h1 className="text-2xl font-semibold text-white mb-2">
                  Check your email
                </h1>
                <p className="text-sm text-zinc-400 mb-6">
                  If an account exists for <strong className="text-zinc-300">{email}</strong>, you'll receive a reset link shortly.
                </p>
                <a
                  href="/login"
                  className="text-sm text-white hover:underline font-medium"
                >
                  Back to sign in
                </a>
              </div>
            ) : (
              <>
                <h1 className="text-2xl font-semibold text-white mb-1">
                  Reset your password
                </h1>
                <p className="text-sm text-zinc-400 mb-8">
                  Enter your email and we'll send a reset link
                </p>

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
                    {loading ? "Sending..." : "Send reset link"}
                  </button>
                </form>

                <p className="text-sm text-center text-zinc-500 mt-6">
                  <a
                    href="/login"
                    className="text-white hover:underline font-medium"
                  >
                    Back to sign in
                  </a>
                </p>
              </>
            )}
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
