import React from "react";
import { Level, LEVEL_NAME } from "../types";

export function LevelPill({ level }: { level: Level }) {
  const cls = level === 3 ? "bg-coral-soft text-coral-deep" : level === 2 ? "bg-sun-soft text-[#9A6B00]" : "bg-leaf-soft text-leaf";
  return <span className={`chip ${cls}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />Level {level} · {LEVEL_NAME[level]}</span>;
}
export function Avatar({ name, size = 40 }: { name: string; size?: number }) {
  const hues = ["bg-coral-soft text-coral-deep", "bg-leaf-soft text-leaf", "bg-sun-soft text-[#9A6B00]", "bg-sky-soft text-sky", "bg-plum-soft text-plum"];
  const h = hues[name.charCodeAt(0) % hues.length];
  return <div style={{ width: size, height: size }} className={`grid shrink-0 place-items-center rounded-full font-display text-lg font-bold ${h}`}>{name[0]}</div>;
}
export function Pulse({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden className={`pointer-events-none absolute ${className}`}>
      {[0, 1, 2].map(i => <span key={i} style={{ animationDelay: `${i * 1.05}s` }} className="absolute inset-0 animate-ring rounded-full border-2 border-coral/60" />)}
      <span className="absolute inset-[38%] rounded-full bg-coral" />
    </div>
  );
}
export function Logo({ light = false }: { light?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <svg width="30" height="30" viewBox="0 0 30 30" aria-hidden>
        <circle cx="15" cy="15" r="13" fill="none" stroke="#2E8B7A" strokeWidth="2" />
        <circle cx="15" cy="15" r="8" fill="none" stroke="#FF7A59" strokeWidth="2" />
        <circle cx="15" cy="15" r="3.4" fill="#FF7A59" />
      </svg>
      <span className={`font-display text-xl font-bold ${light ? "text-white" : "text-ink-800"}`}>EduPulse</span>
    </div>
  );
}
export function SectionTitle({ title, hint, right }: { title: string; hint?: string; right?: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-end justify-between gap-3">
      <div><h2 className="text-xl font-bold">{title}</h2>{hint && <p className="mt-0.5 text-sm text-ink-500">{hint}</p>}</div>{right}
    </div>
  );
}
