import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { studentApi } from "../../api/client";
import { BADGES, BadgeCat } from "../../types";
import { useStore } from "../../store";
import { Medal } from "../../components/Medal";

const cats: BadgeCat[] = ["Effort", "Growth", "Consistency", "Community", "Curiosity"];
const blurb: Record<BadgeCat, string> = {
  Effort: "For showing up and trying",
  Growth: "For beating your own past",
  Consistency: "For steady habits",
  Community: "For lifting others",
  Curiosity: "For asking and exploring",
};

interface BadgeApiItem {
  id: string;
  code: string;
  name: string;
  category: string;
  how_to_earn: string;
  icon: string;
  earned: boolean;
  earned_at?: string;
}

export default function Badges() {
  const { state } = useStore();
  const [sel, setSel] = useState<string | null>(null);

  const { data: serverBadges } = useQuery<BadgeApiItem[]>({
    queryKey: ["student-badges"],
    queryFn: () => studentApi.getBadges(),
  });

  const earnedCodes = new Set(
    serverBadges
      ? serverBadges.filter(b => b.earned).map(b => b.code)
      : []
  );

  const got = earnedCodes.size;

  return (
    <div className="space-y-5">
      <header>
        <p className="label">Badge shelf</p>
        <h1 className="mt-1 text-3xl font-bold">
          {got} of {BADGES.length} found
        </h1>
        <p className="mt-1 text-sm text-ink-500">
          Every badge is earned by effort or growth. Nobody needs top marks to fill this shelf.
        </p>
      </header>

      {cats.map(c => (
        <section key={c}>
          <h2 className="text-lg font-bold">{c}</h2>
          <p className="mb-2 text-xs text-ink-500">{blurb[c]}</p>
          <div className="grid grid-cols-3 gap-3">
            {BADGES.filter(b => b.cat === c).map(b => {
              const has = earnedCodes.has(b.id);
              return (
                <button
                  key={b.id}
                  onClick={() => setSel(sel === b.id ? null : b.id)}
                  aria-pressed={sel === b.id}
                  className={`card flex flex-col items-center p-3 text-center ${
                    sel === b.id ? "ring-2 ring-coral" : ""
                  }`}
                >
                  <Medal badge={b} size={64} locked={!has} />
                  <p className="mt-1 text-[11px] font-bold leading-tight">{b.name}</p>
                </button>
              );
            })}
          </div>
          {BADGES.filter(b => b.cat === c && b.id === sel).map(b => (
            <p key={b.id} className="card mt-2 bg-sun-soft p-3 text-sm" role="status">
              <b>{b.name}:</b> {b.how}
            </p>
          ))}
        </section>
      ))}
    </div>
  );
}
