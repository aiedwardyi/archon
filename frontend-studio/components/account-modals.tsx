"use client"

import { useState } from "react"
import { X, Eye, EyeOff, Check } from "lucide-react"

type ModalProps = { onClose: () => void }

// ─── Shared overlay ───────────────────────────────────────────────────────────
function Modal({ onClose, children }: ModalProps & { children: React.ReactNode }) {
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="relative w-full max-w-md bg-card border border-border rounded-xl shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
        {children}
      </div>
    </div>
  )
}

// ─── Profile Modal ────────────────────────────────────────────────────────────
export function ProfileModal({ onClose }: ModalProps) {
  return (
    <Modal onClose={onClose}>
      <div className="p-6">
        <h2 className="text-lg font-semibold text-foreground mb-5">Profile</h2>
        <div className="flex items-center gap-4 mb-6">
          <div className="h-16 w-16 rounded-full bg-primary flex items-center justify-center shrink-0">
            <span className="text-primary-foreground text-xl font-bold select-none">JD</span>
          </div>
          <div>
            <p className="text-base font-semibold text-foreground">Jane Doe</p>
            <p className="text-sm text-muted-foreground">archon@archon.dev</p>
            <p className="text-xs text-muted-foreground mt-1">Member since January 2025</p>
          </div>
        </div>
        <div className="space-y-3">
          {[
            { label: "Full Name", value: "Jane Doe" },
            { label: "Email", value: "archon@archon.dev" },
            { label: "Plan", value: "Free" },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center justify-between py-2.5 border-b border-border">
              <span className="text-sm text-muted-foreground">{label}</span>
              <span className="text-sm font-medium text-foreground">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </Modal>
  )
}

// ─── Settings Modal ───────────────────────────────────────────────────────────
function MaskedInput({ label, placeholder }: { label: string; placeholder: string }) {
  const [show, setShow] = useState(false)
  const [val, setVal] = useState("")
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-muted-foreground">{label}</label>
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-muted/40">
        <input
          type={show ? "text" : "password"}
          value={val}
          onChange={(e) => setVal(e.target.value)}
          placeholder={placeholder}
          className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground/60 outline-none font-mono"
        />
        <button onClick={() => setShow((s) => !s)} className="text-muted-foreground hover:text-foreground transition-colors">
          {show ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
        </button>
      </div>
    </div>
  )
}

export function SettingsModal({ onClose }: ModalProps) {
  const [saved, setSaved] = useState(false)
  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2000) }
  return (
    <Modal onClose={onClose}>
      <div className="p-6">
        <h2 className="text-lg font-semibold text-foreground mb-1">Settings</h2>
        <p className="text-xs text-muted-foreground mb-5">API keys are stored locally and never sent to our servers.</p>
        <div className="space-y-4 mb-6">
          <MaskedInput label="OpenAI API Key" placeholder="sk-proj-••••••••" />
          <MaskedInput label="Gemini API Key" placeholder="AIza••••••••" />
          <MaskedInput label="Anthropic API Key" placeholder="sk-ant-••••••••" />
        </div>
        <button
          onClick={handleSave}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          {saved ? <><Check className="h-4 w-4" />Saved!</> : "Save API Keys"}
        </button>
      </div>
    </Modal>
  )
}

// ─── Pricing Modal ────────────────────────────────────────────────────────────
export function PricingModal({ onClose }: ModalProps) {
  const plans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      current: true,
      features: ["5 projects", "10 pipeline runs / month", "Basic artifact export", "Community support"],
      cta: "Current Plan",
      ctaDisabled: true,
    },
    {
      name: "Pro",
      price: "$29",
      period: "/ month",
      current: false,
      features: ["Unlimited projects", "Unlimited pipeline runs", "PDF export & shareable links", "White-label client views", "Priority support"],
      cta: "Upgrade to Pro",
      ctaDisabled: false,
    },
  ]
  return (
    <Modal onClose={onClose}>
      <div className="p-6">
        <h2 className="text-lg font-semibold text-foreground mb-1">Pricing</h2>
        <p className="text-xs text-muted-foreground mb-5">Choose the plan that fits your agency.</p>
        <div className="grid grid-cols-2 gap-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-xl border p-4 flex flex-col gap-3 ${
                plan.current
                  ? "border-border bg-muted/30"
                  : "border-primary/40 bg-primary/5"
              }`}
            >
              <div>
                <p className="text-sm font-semibold text-foreground">{plan.name}</p>
                <div className="flex items-baseline gap-1 mt-1">
                  <span className="text-2xl font-bold text-foreground">{plan.price}</span>
                  <span className="text-xs text-muted-foreground">{plan.period}</span>
                </div>
              </div>
              <ul className="space-y-1.5 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-1.5 text-xs text-foreground/70">
                    <Check className="h-3 w-3 text-success mt-0.5 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <button
                disabled={plan.ctaDisabled}
                className={`mt-auto w-full py-2 rounded-lg text-xs font-medium transition-colors ${
                  plan.ctaDisabled
                    ? "bg-muted text-muted-foreground cursor-not-allowed"
                    : "bg-primary text-primary-foreground hover:bg-primary/90"
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </Modal>
  )
}
