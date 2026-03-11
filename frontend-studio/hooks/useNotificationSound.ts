import { useCallback, useEffect, useRef } from "react";

export function useNotificationSound() {
  const audioContextRef = useRef<AudioContext | null>(null);

  const ensureAudioContext = useCallback(async () => {
    if (typeof window === "undefined") return null;

    const AudioContextCtor =
      window.AudioContext ||
      (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;

    if (!AudioContextCtor) return null;

    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContextCtor();
    }

    const ctx = audioContextRef.current;
    if (ctx.state === "suspended") {
      try {
        await ctx.resume();
      } catch {
        return null;
      }
    }

    return ctx;
  }, []);

  useEffect(() => {
    const unlockAudio = () => {
      void ensureAudioContext();
    };

    window.addEventListener("pointerdown", unlockAudio, { passive: true });
    window.addEventListener("keydown", unlockAudio);

    return () => {
      window.removeEventListener("pointerdown", unlockAudio);
      window.removeEventListener("keydown", unlockAudio);
      const ctx = audioContextRef.current;
      audioContextRef.current = null;
      if (ctx && ctx.state !== "closed") {
        void ctx.close();
      }
    };
  }, [ensureAudioContext]);

  const playSuccess = useCallback(async () => {
    const ctx = await ensureAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const notes: [number, number][] = [[523, 0.15], [659, 0.15], [784, 0.3]];
    let offset = 0;
    for (const [freq, dur] of notes) {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.25, now + offset);
      gain.gain.linearRampToValueAtTime(0, now + offset + dur);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + offset);
      osc.stop(now + offset + dur + 0.01);
      offset += dur;
    }
  }, [ensureAudioContext]);

  const playFailure = useCallback(async () => {
    const ctx = await ensureAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(330, now);
    osc.frequency.linearRampToValueAtTime(220, now + 0.3);
    gain.gain.setValueAtTime(0.25, now);
    gain.gain.linearRampToValueAtTime(0, now + 0.3);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 0.31);
  }, [ensureAudioContext]);

  return { playSuccess, playFailure };
}
