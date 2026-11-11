import { useEffect, useRef, useState } from "react";

/** Interpola suavemente entre valores numericos (sensacao de instrumento vivo). Respeita prefers-reduced-motion. */
export function useTween(target: number, ms = 450): number {
  const [v, setV] = useState(target);
  const from = useRef(target);
  const raf = useRef(0);
  useEffect(() => {
    const reduce = typeof matchMedia !== "undefined" && matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce || !Number.isFinite(target) || Math.abs(target - from.current) < 1e-9) { from.current = target; setV(target); return; }
    const a = from.current, t0 = performance.now();
    const tick = (now: number) => {
      const k = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - k, 3);
      const cur = a + (target - a) * e;
      from.current = cur; setV(cur);
      if (k < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [target, ms]);
  return v;
}
