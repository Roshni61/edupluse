import React from "react";
export function Garden({ pct, drops = 0 }: { pct: number; drops?: number }) {
  const stage = pct >= 0.9 ? 4 : pct >= 0.6 ? 3 : pct >= 0.25 ? 2 : pct > 0 ? 1 : 0;
  const h = [4, 20, 42, 64, 78][stage];
  const xs = [48, 105, 160, 215, 262];
  const cols = ["#FF7A59", "#F4B942", "#8B5CF6", "#FF7A59", "#F4B942"];
  return (
    <svg viewBox="0 0 310 170" className="w-full" role="img" aria-label={`Class garden at stage ${stage + 1} of 5`}>
      <defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#E3EEFF" /><stop offset="1" stopColor="#F7FAF9" /></linearGradient></defs>
      <rect width="310" height="170" rx="22" fill="url(#sky)" />
      <circle cx="268" cy="34" r="16" fill="#F4B942" opacity=".85" />
      {stage === 4 && <g><rect x="147" y="70" width="14" height="70" rx="6" fill="#8A5A3C" /><circle cx="154" cy="62" r="34" fill="#2E8B7A" /><circle cx="128" cy="78" r="22" fill="#3AA390" /><circle cx="180" cy="78" r="22" fill="#3AA390" /></g>}
      <ellipse cx="155" cy="150" rx="150" ry="20" fill="#8A5A3C" opacity=".9" />
      <ellipse cx="155" cy="144" rx="150" ry="18" fill="#9C6B49" />
      {xs.map((x, i) => (
        <g key={i} style={{ transition: "all .8s ease" }}>
          <rect x={x - 2} y={142 - h} width="4" height={h} rx="2" fill="#2E8B7A" />
          {stage >= 1 && <ellipse cx={x - 9} cy={142 - h * 0.45} rx="9" ry="4.5" fill="#3AA390" transform={`rotate(-28 ${x - 9} ${142 - h * 0.45})`} />}
          {stage >= 1 && <ellipse cx={x + 9} cy={142 - h * 0.65} rx="9" ry="4.5" fill="#2E8B7A" transform={`rotate(28 ${x + 9} ${142 - h * 0.65})`} />}
          {stage >= 3 && <g><circle cx={x} cy={142 - h - 3} r="9" fill={cols[i]} /><circle cx={x} cy={142 - h - 3} r="3.6" fill="#fff" opacity=".85" /></g>}
        </g>
      ))}
      {Array.from({ length: Math.min(drops, 5) }).map((_, i) => (
        <path key={i} d="M0 0 C4 6 7 9 7 12 A7 7 0 1 1 -7 12 C-7 9 -4 6 0 0Z" transform={`translate(${40 + i * 28} ${18 + (i % 2) * 14})`} fill="#4C8DFF" opacity=".8" className="animate-floaty" />
      ))}
    </svg>
  );
}
export function gardenStage(pct: number) { return ["Seeds", "Sprouts", "Saplings", "In bloom", "A full grove"][pct >= 0.9 ? 4 : pct >= 0.6 ? 3 : pct >= 0.25 ? 2 : pct > 0 ? 1 : 0]; }
