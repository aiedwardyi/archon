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

  const playTone = useCallback(
    async (freqs: [number, number?], durationMs: number, volume = 0.25) => {
      const ctx = await ensureAudioContext();
      if (!ctx) return;
      const now = ctx.currentTime;
      const dur = durationMs / 1000;

      freqs.forEach((freq, i) => {
        if (freq == null) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.value = freq;

        if (freqs.length === 1 && freqs[1] === undefined) {
          // single descending tone — ramp frequency
          osc.frequency.setValueAtTime(freqs[0]!, now);
          osc.frequency.linearRampToValueAtTime(220, now + dur);
        }

        gain.gain.setValueAtTime(volume, now + i * 0.15);
        gain.gain.linearRampToValueAtTime(0, now + i * 0.15 + dur);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + i * 0.15);
        osc.stop(now + i * 0.15 + dur + 0.01);
      });
    },
    [ensureAudioContext]
  );

  const playSuccess = useCallback(async () => {
    await playTone([440, 660], 150, 0.25);
  }, [playTone]);

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
