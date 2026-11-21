import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Clock, ChevronRight, PartyPopper, Droplets, PhoneCall, Check, AlertCircle, RefreshCw } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { teacherApi } from "../../api/client";
import { useStore } from "../../store";
import { Avatar, LevelPill, SectionTitle } from "../../components/ui";
import { Ring } from "../../components/Ring";
import { EmptyState } from "../../components/EmptyState";

interface StudentItem {
  id: string;
  name: string;
  subject: string;
  support_level: 1 | 2 | 3;
  reasons: string[];
  suggested_actions: string[];
  minutes: number;
  benefit: number;
  bright: boolean;
  bright_why?: string;
  parent_who: string;
  parent_channel: string;
}

interface BrightSpot {
  id: string;
  name: string;
  bright_why?: string;
  kudos_sent: boolean;
}

interface TodayData {
  budget: number;
  used: number;
  in_plan: StudentItem[];
  later: StudentItem[];
  bright: BrightSpot[];
  summary: {
    class_name: string;
    total_students: number;
    watered_yesterday: number;
    parents_reached: number;
    garden_drops: number;
    target_garden_drops: number;
  };
}

export default function Dashboard() {
  const [budget, setBudget] = useState<number>(20);
  const { state, dispatch } = useStore();
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error, refetch } = useQuery<TodayData>({
    queryKey: ["teacher-today", budget],
    queryFn: () => teacherApi.getTodayPlan(budget),
  });

  const kudosMutation = useMutation({
    mutationFn: (studentId: string) => teacherApi.sendKudos(studentId),
    onSuccess: (_, studentId) => {
      dispatch({ t: "kudos", id: studentId });
      queryClient.invalidateQueries({ queryKey: ["teacher-today"] });
      queryClient.invalidateQueries({ queryKey: ["bright-spots"] });
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="h-4 w-32 rounded bg-sage-2"></div>
            <div className="mt-2 h-9 w-64 rounded-xl bg-sage-2"></div>
            <div className="mt-2 h-4 w-80 rounded bg-sage-2"></div>
          </div>
          <div className="h-14 w-44 rounded-2xl bg-sage-2"></div>
        </div>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="card h-28 p-5 bg-white"></div>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="card flex flex-col items-center justify-center p-8 text-center space-y-4">
        <AlertCircle size={40} className="text-coral" />
        <h2 className="text-xl font-bold">Failed to load today's plan</h2>
        <p className="text-sm text-ink-500 max-w-md">{(error as Error)?.message || "Could not connect to the EduPulse server."}</p>
        <button onClick={() => refetch()} className="btn-primary !px-4 !py-2">
          <RefreshCw size={15} /> Try again
        </button>
      </div>
    );
  }

  const inPlan = data?.in_plan || [];
  const later = data?.later || [];
  const bright = data?.bright || [];
  const used = data?.used ?? 0;
  const summary = data?.summary || {
    class_name: "9A",
    total_students: 24,
    watered_yesterday: 18,
    parents_reached: 21,
    garden_drops: 31,
    target_garden_drops: 48,
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="label">Thursday, 19 November</p>
          <h1 className="mt-1 text-4xl font-bold">Good morning, Ms. Priya</h1>
          <p className="mt-1 text-ink-500">
            Class {summary.class_name} · {summary.total_students} students · {summary.watered_yesterday} of {summary.total_students} watered the Garden yesterday
          </p>
        </div>
        <div className="card flex items-center gap-4 p-3 pr-4">
          <Clock className="ml-1 text-coral" />
          <div>
            <p className="label">Your time today</p>
            <div className="mt-1 flex gap-1.5" role="radiogroup" aria-label="Time budget">
              {[10, 20, 30].map(m => (
                <button
                  key={m}
                  role="radio"
                  aria-checked={budget === m}
                  onClick={() => {
                    setBudget(m);
                    dispatch({ t: "budget", v: m });
                  }}
                  className={`rounded-xl px-3.5 py-1.5 text-sm font-bold ${
                    budget === m ? "bg-ink-800 text-white" : "bg-sage text-ink-700 hover:bg-sage-2"
                  }`}
                >
                  {m} min
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <section>
        <SectionTitle
          title={`Your plan for ${budget} minutes`}
          hint={`${used} minutes planned. Ranked by how much your time helps, not just by how urgent it looks.`}
        />
        <div className="space-y-3">
          {inPlan.length === 0 ? (
            <EmptyState
              icon={Clock}
              title="No students need immediate intervention"
              description={`For the selected ${budget}-minute budget, all students in Class ${summary.class_name} are progressing well.`}
            />
          ) : (
            inPlan.map((s, i) => {
            const done = false;
            const primaryReason = s.reasons?.[0] || "Identified for regular check-in";
            const suggestedAction = s.suggested_actions?.[0] || "5-minute check-in";
            return (
              <article key={s.id} className="card flex flex-wrap items-center gap-4 p-4 md:flex-nowrap md:p-5">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-ink-800 font-display font-bold text-white">
                  {i + 1}
                </span>
                <Avatar name={s.name} size={48} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-lg font-bold">{s.name}</h3>
                    <LevelPill level={s.support_level} />
                  </div>
                  <p className="mt-1 text-sm text-ink-700">{primaryReason}</p>
                  <p className="mt-0.5 text-sm text-ink-500">Suggested: {suggestedAction}</p>
                </div>
                <div className="flex w-full items-center justify-between gap-3 md:w-auto md:flex-col md:items-end">
                  <span className="chip bg-sage text-ink-700">
                    <Clock size={13} />
                    {s.minutes} min
                  </span>
                  {done ? (
                    <span className="chip bg-leaf-soft text-leaf">
                      <Check size={13} />
                      Logged
                    </span>
                  ) : (
                    <Link to={`/teacher/student/${s.id}`} className="btn-primary !px-4 !py-2">
                      Open <ChevronRight size={16} />
                    </Link>
                  )}
                </div>
              </article>
            );
          })
          )}
        </div>
        {later.length > 0 && (
          <details className="card mt-3 p-4">
            <summary className="cursor-pointer text-sm font-bold text-ink-700">
              Can wait until tomorrow ({later.length})
            </summary>
            <ul className="mt-3 space-y-2">
              {later.map(s => (
                <li key={s.id} className="flex items-center justify-between rounded-2xl bg-sage px-4 py-2.5 text-sm">
                  <span className="font-semibold">
                    {s.name}
                    <span className="ml-2 font-normal text-ink-500">{s.reasons?.[0] || "On tracking watchlist"}</span>
                  </span>
                  <Link className="font-bold text-ink-800 underline" to={`/teacher/student/${s.id}`}>
                    Open
                  </Link>
                </li>
              ))}
            </ul>
          </details>
        )}
      </section>

      <div className="grid gap-6 lg:grid-cols-5">
        <section className="lg:col-span-3">
          <SectionTitle
            title="Bright spots"
            hint="Progress worth celebrating. A kind word from you lands harder than any badge."
          />
          <div className="grid gap-3 sm:grid-cols-2">
            {bright.map(s => {
              const hasKudos = s.kudos_sent;
              return (
                <div key={s.id} className="card flex items-center gap-4 p-4">
                  <Avatar name={s.name} size={44} />
                  <div className="min-w-0 flex-1">
                    <h3 className="font-bold">{s.name}</h3>
                    <p className="text-sm text-ink-500">{s.bright_why || "Steady progress"}</p>
                  </div>
                  <button
                    disabled={hasKudos || kudosMutation.isPending}
                    onClick={() => kudosMutation.mutate(s.id)}
                    className="btn-soft !px-3 !py-2 disabled:opacity-60"
                  >
                    <PartyPopper size={16} />
                    {hasKudos ? "Sent" : "Kudos"}
                  </button>
                </div>
              );
            })}
          </div>
        </section>
        <section className="lg:col-span-2">
          <SectionTitle title="This week" />
          <div className="card grid grid-cols-2 gap-4 p-5">
            <div className="flex flex-col items-center text-center">
              <Ring pct={summary.parents_reached / summary.total_students} size={96} stroke={10} color="#2E8B7A">
                <span className="font-display text-xl font-bold">
                  {summary.parents_reached}/{summary.total_students}
                </span>
              </Ring>
              <p className="mt-2 text-xs font-semibold text-ink-500">Parents reached</p>
            </div>
            <div className="flex flex-col items-center text-center">
              <Ring pct={summary.garden_drops / summary.target_garden_drops} size={96} stroke={10}>
                <Droplets className="text-sky" />
              </Ring>
              <p className="mt-2 text-xs font-semibold text-ink-500">
                Garden {summary.garden_drops} of {summary.target_garden_drops} drops
              </p>
            </div>
            <Link to="/teacher/connect" className="btn-soft col-span-2">
              <PhoneCall size={16} />3 parents need a human touch
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
