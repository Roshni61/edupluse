import React, { useMemo } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useStore } from "../store";
import { BADGES } from "../types";
import { Medal } from "./Medal";

export function Celebrate() {
  const { state, dispatch } = useStore();
  const badge = BADGES.find(b => b.id === state.unlock);
  const bits = useMemo(() => Array.from({ length: 34 }, (_, i) => ({ x: (i * 53) % 100, d: 0.9 + ((i * 7) % 10) / 10, c: ["#FF7A59", "#F4B942", "#2E8B7A", "#4C8DFF", "#8B5CF6"][i % 5], r: (i * 37) % 360 })), [state.unlock]);
  return (
    <AnimatePresence>
      {badge && (
        <motion.div className="fixed inset-0 z-50 grid place-items-center bg-ink-900/60 p-5 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => dispatch({ t: "clearUnlock" })}>
          {bits.map((b, i) => (
            <motion.span key={i} className="absolute top-0 h-3 w-2 rounded-sm" style={{ left: `${b.x}%`, background: b.c }}
              initial={{ y: -20, rotate: 0, opacity: 1 }} animate={{ y: 900, rotate: b.r + 360, opacity: 0.9 }} transition={{ duration: 2.2 + b.d, ease: "easeIn" }} />
          ))}
          <motion.div role="dialog" aria-label="Badge unlocked" className="card w-full max-w-xs p-7 text-center" initial={{ scale: 0.7, y: 30 }} animate={{ scale: 1, y: 0 }} transition={{ type: "spring", stiffness: 260, damping: 18 }} onClick={e => e.stopPropagation()}>
            <p className="label text-coral-deep">New badge</p>
            <motion.div className="mx-auto mt-4 w-fit" initial={{ rotate: -14, scale: 0.6 }} animate={{ rotate: 0, scale: 1 }} transition={{ type: "spring", stiffness: 200, damping: 10, delay: 0.15 }}>
              <Medal badge={badge} size={132} />
            </motion.div>
            <h3 className="mt-3 text-2xl font-bold">{badge.name}</h3>
            <p className="mt-1 text-sm text-ink-500">{badge.how}</p>
            <button className="btn-coral mt-5 w-full" onClick={() => dispatch({ t: "clearUnlock" })}>Keep going</button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
export function Toast() {
  const { state } = useStore();
  return (
    <AnimatePresence>
      {state.toast && (
        <motion.div role="status" className="fixed bottom-24 left-1/2 z-50 w-[min(92vw,420px)] -translate-x-1/2 rounded-2xl bg-ink-800 px-5 py-3.5 text-sm font-medium text-white shadow-soft lg:bottom-8"
          initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 16 }}>{state.toast}</motion.div>
      )}
    </AnimatePresence>
  );
}
