import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Clock, Zap, HelpCircle, Heart, Check, ChevronRight, X, Moon, AlertCircle, RefreshCw } from "lucide-react";
import { Area, AreaChart, ResponsiveContainer, XAxis } from "recharts";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { studentApi } from "../../api/client";
import { BADGES } from "../../types";
import { useStore } from "../../store";
import { Ring } from "../../components/Ring";
import { Medal } from "../../components/Medal";
import { Garden, gardenStage } from "../../components/Garden";
import { EmptyState } from "../../components/EmptyState";

interface MissionItem {
  id: string;
  title: string;
  minutes: number;
  xp: number;
  tier: string;
  kind: string;
  blurb: string;
  is_done: boolean;
  badge_id?: string;
}

interface BadgeItem {
  id: string;
  code: string;
  name: string;
  category: string;
  how_to_earn: string;
  icon: string;
  earned: boolean;
}

interface HomeData {
  xp_total: number;
  level_name: string;
  next_level: string;
  to_next: number;
  pct: number;
  class_name: string;
  student_name: string;
  assigned_missions: MissionItem[];
  earned_badges: BadgeItem[];
  total_badges_count: number;
  class_garden: {
    total_drops: number;
    target_drops: number;
    stage: string;
    pct: number;
    watered_today_count: number;
    total_classmates: number;
  };
  recent_kudos: {
    id: string;
    teacher_name: string;
    message: string;
    created_at: string;
  }[];
  own_progress: { w: string; v: number }[];
}

export default function StudentHome() {
  const { state, dispatch } = useStore();
  const queryClient = useQueryClient();
  const [stuck, setStuck] = useState<boolean>(false);

  const { data, isLoading, isError, error, refetch } = useQuery<HomeData>({
    queryKey: ["student-home"],
    queryFn: () => studentApi.getHome(),
  });

  const doubtMutation = useMutation({
    mutationFn: (topic: string) =>
      studentApi.postDoubt({ text: `${topic} - submitted via I'm stuck dialog`, topic }),
    onSuccess: () => {
      setStuck(false);
      dispatch({ t: "toast", v: "Sent anonymously. Thank you for telling us." });
      queryClient.invalidateQueries({ queryKey: ["student-home"] });
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-5 animate-pulse">
        <div className="flex items-start justify-between">
          <div>
            <div className="h-4 w-20 rounded bg-sage-2"></div>
            <div className="mt-2 h-8 w-44 rounded-xl bg-sage-2"></div>
          </div>
          <div className="h-9 w-24 rounded-2xl bg-sage-2"></div>
        </div>
        <div className="card h-36 bg-white p-5"></div>
        <div className="space-y-2.5">
          {[1, 2, 3].map(i => (
            <div key={i} className="card h-20 bg-white p-3.5"></div>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="card flex flex-col items-center justify-center p-8 text-center space-y-4">
        <AlertCircle size={40} className="text-coral" />
        <h2 className="text-xl font-bold">Could not load home screen</h2>
        <p className="text-sm text-ink-500 max-w-md">{(error as Error)?.message || "Please check server connection."}</p>
        <button onClick={() => refetch()} className="btn-primary !px-4 !py-2">
          <RefreshCw size={15} /> Try again
        </button>
      </div>
    );
  }

  const xpTotal = data?.xp_total ?? 0;
  const levelName = data?.level_name ?? "Sprout";
  const nextLevel = data?.next_level ?? "Sapling";
  const toNext = data?.to_next ?? 0;
  const levelPct = data?.pct ?? 0;
  const studentName = data?.student_name ?? "Student";
  const className = data?.class_name ?? "";

  const missions = data?.assigned_missions ?? [];
  const doneMissionsCount = missions.filter(m => m.is_done).length;
  const totalMissionsCount = missions.length;

  const earnedBadges = data?.earned_badges ?? [];
  const gardenDrops = data?.class_garden.total_drops ?? 0;
  const gardenPct = data?.class_garden.pct ?? (gardenDrops / 48);
  const ownProgress = data?.own_progress ?? [
    { w: "Wk 1", v: 40 },
    { w: "Wk 2", v: 48 },
    { w: "Wk 3", v: 45 },
    { w: "Wk 4", v: 58 },
    { w: "Wk 5", v: 65 },
  ];

  const recentKudo = data?.recent_kudos?.[0];

  return (
    <div className="space-y-5">
      <header className="flex items-start justify-between">
        <div>
          <p className="label">Class {className}</p>
          <h1 className="mt-1 text-3xl font-bold">Hi {studentName}</h1>
          <p className="text-sm text-ink-500">Small steps count. Let's grow something today.</p>
        </div>
        <button onClick={() => setStuck(true)} className="btn-soft !px-3 !py-2 text-xs">
          <HelpCircle size={15} />
          I'm stuck
        </button>
      </header>

      <section className="card relative overflow-hidden bg-ink-800 p-5 text-white">
        <div className="flex items-center gap-4">
          <Ring pct={levelPct} size={104} stroke={10} color="#FF7A59">
            <div>
              <p className="font-display text-2xl font-bold text-white">{xpTotal}</p>
              <p className="-mt-1 text-[10px] font-bold uppercase tracking-widest text-white/70">XP</p>
            </div>
          </Ring>
          <div>
            <p className="label !text-coral">Level</p>
            <h2 className="text-2xl font-bold !text-white">{levelName}</h2>
            <p className="mt-1 text-sm text-white/75">
              {toNext > 0 ? `${toNext} XP to ${nextLevel}` : "Top level reached!"}
            </p>
            <p className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-[11px] font-semibold">
              <Moon size={12} />
              Rest days never break your streak
            </p>
          </div>
        </div>
      </section>

      <section>
        <div className="mb-2 flex items-end justify-between">
          <h2 className="text-xl font-bold">Today's missions</h2>
          <span className="text-xs font-semibold text-ink-500">
            {doneMissionsCount} of {totalMissionsCount} done
          </span>
        </div>
        <div className="space-y-2.5">
          {missions.length === 0 ? (
            <EmptyState
              icon={Zap}
              title="All caught up!"
              description="No active missions right now. Check back tomorrow or explore your badge shelf!"
            />
          ) : (
            missions.map(m => {
              const isDone = m.is_done;
              return (
                <div key={m.id} className={`card flex items-center gap-3 p-3.5 ${isDone ? "bg-leaf-soft" : ""}`}>
                  <span
                    className={`grid h-11 w-11 shrink-0 place-items-center rounded-2xl ${
                      isDone ? "bg-leaf text-white" : "bg-coral-soft text-coral-deep"
                    }`}
                  >
                    {isDone ? <Check size={20} /> : <Zap size={20} />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-bold leading-tight">{m.title}</p>
                    <p className="mt-0.5 flex items-center gap-2 text-xs text-ink-500">
                      <Clock size={12} />
                      {m.minutes} min
                      <span className="chip !px-2 !py-0.5 bg-sage text-ink-700">{m.tier}</span>
                      +{m.xp} XP
                    </p>
                  </div>
                  {!isDone && (
                    <Link
                      to={`/student/play/${m.id}`}
                      className="btn-coral !px-3.5 !py-2"
                      aria-label={`Start ${m.title}`}
                    >
                      Start
                      <ChevronRight size={15} />
                    </Link>
                  )}
                </div>
              );
            })
          )}
        </div>
      </section>

      <section className="card p-4">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-lg font-bold">Your own progress</h2>
            <p className="text-xs text-ink-500">Practice progress, compared with your past self</p>
          </div>
          <p className="font-display text-2xl font-bold text-leaf">+25</p>
        </div>
        <div className="mt-2 h-24">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={ownProgress} margin={{ left: 0, right: 0, top: 6, bottom: 0 }}>
              <defs>
                <linearGradient id="gp" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0" stopColor="#2E8B7A" stopOpacity={0.5} />
                  <stop offset="1" stopColor="#2E8B7A" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="w" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
              <Area type="monotone" dataKey="v" stroke="#2E8B7A" strokeWidth={3} fill="url(#gp)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section>
        <div className="mb-2 flex items-end justify-between">
          <h2 className="text-xl font-bold">My badges</h2>
          <Link to="/student/badges" className="text-sm font-bold text-ink-700 underline">
            See all
          </Link>
        </div>
        <div className="card flex gap-4 overflow-x-auto p-4">
          {earnedBadges.map(b => (
            <div key={b.id} className="flex w-20 shrink-0 flex-col items-center text-center">
              <Medal badge={b as any} size={64} />
              <p className="mt-1 text-[11px] font-bold leading-tight">{b.name}</p>
            </div>
          ))}
          <Link
            to="/student/badges"
            className="grid w-20 shrink-0 place-items-center rounded-2xl border-2 border-dashed border-sage-2 text-center text-[11px] font-bold text-ink-500"
          >
            {Math.max(0, 12 - earnedBadges.length)} more to find
          </Link>
        </div>
      </section>

      <section className="card p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Class Garden</h2>
          <span className="chip bg-sky-soft text-sky">{gardenStage(gardenPct)}</span>
        </div>
        <Garden pct={gardenPct} drops={Math.min(5, doneMissionsCount + 2)} />
        <p className="mt-2 text-sm text-ink-500">
          {gardenDrops} drops watered by the class so far. Everyone's drops count the same.
        </p>
      </section>

      {recentKudo ? (
        <section className="card flex gap-3 bg-sun-soft p-4">
          <Heart className="mt-0.5 shrink-0 text-coral-deep" size={20} />
          <div>
            <p className="label !text-[#9A6B00]">From {recentKudo.teacher_name}</p>
            <p className="mt-1 text-sm leading-relaxed">{recentKudo.message}</p>
          </div>
        </section>
      ) : (
        <section className="card flex gap-3 bg-sun-soft p-4">
          <Heart className="mt-0.5 shrink-0 text-coral-deep" size={20} />
          <div>
            <p className="label !text-[#9A6B00]">From Ms. Priya</p>
            <p className="mt-1 text-sm leading-relaxed">
              I noticed you kept going on the fractions even when it got tricky. That's exactly how it gets easier.
            </p>
          </div>
        </section>
      )}

      {stuck && (
        <div
          className="fixed inset-0 z-50 grid place-items-center bg-ink-900/60 p-5"
          role="dialog"
          aria-label="I'm stuck"
          onClick={() => setStuck(false)}
        >
          <div className="card w-full max-w-sm p-6" onClick={e => e.stopPropagation()}>
            <div className="flex justify-between">
              <h3 className="text-xl font-bold">It's okay to be stuck</h3>
              <button onClick={() => setStuck(false)} aria-label="Close">
                <X size={20} />
              </button>
            </div>
            <p className="mt-2 text-sm text-ink-500">
              Tell us what feels hard. Your teacher sees it as an anonymous note, without your name on it.
            </p>
            <div className="mt-4 grid gap-2">
              {["A topic is confusing", "I need more time", "Something else is going on"].map(t => (
                <button
                  key={t}
                  disabled={doubtMutation.isPending}
                  onClick={() => doubtMutation.mutate(t)}
                  className="btn-soft justify-start"
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
