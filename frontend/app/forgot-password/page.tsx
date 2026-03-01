"use client";
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
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
            <polygon points="12,2 20.66,7 20.66,17 12,22 3.34,17 3.34,7"
              fill="none" stroke="#3b82f6" strokeWidth="2" strokeLinejoin="round"/>
          </svg>
          <span className="text-xl font-bold tracking-tight">Archon</span>
        </div>
        <div className="border border-border rounded-lg p-6 bg-card">
          {sent ? (
            <div className="text-center">
              <div className="text-2xl mb-3">📧</div>
              <h1 className="text-lg font-semibold mb-2">Check your email</h1>
              <p className="text-sm text-muted-foreground mb-4">
                If an account exists for <strong>{email}</strong>, you'll receive a reset link shortly.
              </p>
              <a href="/login" className="text-sm text-primary hover:underline">Back to sign in</a>
            </div>
          ) : (
            <>
              <h1 className="text-lg font-semibold mb-1">Reset password</h1>
              <p className="text-sm text-muted-foreground mb-6">Enter your email and we'll send a reset link.</p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-1.5 block">Email</label>
                  <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                    placeholder="you@example.com" required
                    className="w-full px-3 py-2 text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary/30" />
                </div>
                {error && <div className="text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-md px-3 py-2">{error}</div>}
                <button type="submit" disabled={loading}
                  className="w-full py-2 px-4 bg-primary text-primary-foreground text-sm font-medium rounded-md hover:bg-primary/90 disabled:opacity-50 transition-colors">
                  {loading ? "Sending..." : "Send reset link"}
                </button>
              </form>
              <p className="text-sm text-center text-muted-foreground mt-4">
                <a href="/login" className="text-primary hover:underline">Back to sign in</a>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
