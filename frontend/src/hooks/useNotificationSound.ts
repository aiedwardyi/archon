import { useCallback } from "react";

export function useNotificationSound() {
  const playTone = useCallback(
    (freqs: [number, number?], durationMs: number, volume = 0.25) => {
      const ctx = new AudioContext();
      const now = ctx.currentTime;
      const dur = durationMs / 1000;

      freqs.forEach((freq, i) => {
        if (freq == null) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.value = freq;

        if (freqs.length === 1 && freqs[1] === undefined) {
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
    []
  );

  const playSuccess = useCallback(() => {
    // 3-tone ascending chime matching notify.ps1: C5 → E5 → G5
    const ctx = new AudioContext();
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
  }, []);

  const playFailure = useCallback(() => {
    const ctx = new AudioContext();
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
  }, []);

  return { playSuccess, playFailure };
}
