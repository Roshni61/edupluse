import React from "react";
import { Footprints, Sun, RotateCcw, TrendingUp, Rocket, Target, CalendarCheck, Sunrise, HeartHandshake, Sprout, MessageCircleQuestion, Compass, Star, Lock, type LucideIcon } from "lucide-react";
type IC = LucideIcon;
const ICONS: Record<string, IC> = { Footprints, Sun, RotateCcw, TrendingUp, Rocket, Target, CalendarCheck, Sunrise, HeartHandshake, Sprout, MessageCircleQuestion, Compass };
import { Badge, BadgeCat } from "../types";

const PAL: Record<BadgeCat, { a: string; b: string; ring: string }> = {
  Effort: { a: "#FF9A7D", b: "#E85D3A", ring: "#FFD3C6" },
  Growth: { a: "#4FB8A5", b: "#1F7766", ring: "#BDEBDF" },
  Consistency: { a: "#F8CD6B", b: "#D9980F", ring: "#FCE7B0" },
  Community: { a: "#7FB0FF", b: "#2F6FE0", ring: "#CFE0FF" },
  Curiosity: { a: "#B69BFF", b: "#6D3FE0", ring: "#DDD2FF" },
};
export function Medal({ badge, size = 88, locked = false }: { badge: any; size?: number; locked?: boolean }) {
  const cat = (badge.cat || badge.category || "Effort") as BadgeCat;
  const p = PAL[cat] || PAL.Effort;
  const Icon = ICONS[badge.icon] ?? Star;
  const id = `g-${badge.id || badge.code || Math.random().toString(36).substring(2, 9)}`;
  return (
    <div style={{ width: size, height: size * 1.12 }} className={`relative ${locked ? "opacity-60 saturate-0" : ""}`}>
      <svg viewBox="0 0 100 112" width="100%" height="100%" aria-hidden>
        <defs><linearGradient id={id} x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor={p.a} /><stop offset="1" stopColor={p.b} /></linearGradient></defs>
        <path d="M30 4 L50 40 L70 4 L84 8 L58 56 L42 56 L16 8 Z" fill={p.b} opacity=".85" />
        <circle cx="50" cy="66" r="40" fill={`url(#${id})`} />
        <circle cx="50" cy="66" r="33" fill="none" stroke={p.ring} strokeWidth="2.5" strokeDasharray="3 4" />
        <ellipse cx="38" cy="48" rx="16" ry="7" fill="#fff" opacity=".22" transform="rotate(-24 38 48)" />
      </svg>
      <div className="absolute left-0 right-0 grid place-items-center" style={{ top: size * 0.46 }}>
        {locked ? <Lock size={size * 0.3} color="#fff" /> : <Icon size={size * 0.36} color="#fff" strokeWidth={2.2} />}
      </div>
    </div>
  );
}
