import React, { useState } from "react";
import { Printer, Check, Send, CheckSquare } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { teacherApi, gardenApi } from "../../api/client";
import { BADGES } from "../../types";
import { useStore } from "../../store";
import { SectionTitle } from "../../components/ui";
import { Garden, gardenStage } from "../../components/Garden";
import { Medal } from "../../components/Medal";
import { EmptyState } from "../../components/EmptyState";

interface MissionItem {
  id: string;
  title: string;
  minutes: number;
  xp: number;
  tier: string;
  kind: string;
  blurb: string;
  is_assigned: boolean;
}

interface StudentItem {
  id: string;
  name: string;
  support_level: number;
  bright: boolean;
}

export default function Missions() {
  const { state, dispatch } = useStore();
  const queryClient = useQueryClient();
  const [selectedStudentForTick, setSelectedStudentForTick] = useState<string>("");
  const [tickSuccess, setTickSuccess] = useState<string | null>(null);
  const [sentKudos, setSentKudos] = useState<string[]>([]);

  const { data: missionsData, isLoading: missionsLoading } = useQuery<MissionItem[]>({
    queryKey: ["teacher-missions"],
    queryFn: () => teacherApi.getMissions(),
  });

  const { data: gardenData } = useQuery({
    queryKey: ["class-garden"],
    queryFn: () => gardenApi.getClassGarden("9A"),
  });

  const { data: studentsData } = useQuery<StudentItem[]>({
    queryKey: ["teacher-students"],
    queryFn: () => teacherApi.getStudents(),
  });

  const assignMutation = useMutation({
    mutationFn: ({ missionId, assign }: { missionId: string; assign: boolean }) =>
      teacherApi.assignMission(missionId, assign),
    onSuccess: (_, vars) => {
      dispatch({ t: "assign", id: vars.missionId });
      queryClient.invalidateQueries({ queryKey: ["teacher-missions"] });
    },
  });

  const tickMutation = useMutation({
    mutationFn: ({ missionId, studentId }: { missionId: string; studentId: string }) =>
      teacherApi.tickMission(missionId, studentId, "Paper mission verified"),
    onSuccess: res => {
      setTickSuccess(res.message);
      queryClient.invalidateQueries({ queryKey: ["class-garden"] });
      setTimeout(() => setTickSuccess(null), 4000);
    },
  });

  const kudosMutation = useMutation({
    mutationFn: (studentId: string) => teacherApi.sendKudos(studentId),
    onSuccess: (_, studentId) => {
      setSentKudos(prev => [...prev, studentId]);
      dispatch({ t: "kudos", id: studentId });
      queryClient.invalidateQueries({ queryKey: ["teacher-students"] });
    },
  });

  const missions = missionsData || [
    { id: "m1", title: "Fraction warm-up", minutes: 5, xp: 30, tier: "Starter", kind: "quiz", blurb: "Three friendly questions. No marks lost for wrong answers.", is_assigned: true },
    { id: "m2", title: "Explain it to a friend", minutes: 3, xp: 20, tier: "Starter", kind: "help", blurb: "Pick one idea from today and explain it to a classmate.", is_assigned: true },
    { id: "m3", title: "Ask one doubt", minutes: 2, xp: 15, tier: "Starter", kind: "ask", blurb: "Anything you're unsure about. Your teacher sees it without your name on it.", is_assigned: true },
  ];

  const totalDrops = gardenData?.total_drops ?? 0;
  const pct = totalDrops / 48;

  const eligibleKudosStudents = (studentsData || []).filter(s => s.support_level >= 2 || s.bright).slice(0, 6);

  return (
    <div className="space-y-8">
      <div className="no-print">
        <p className="label">Missions and Garden</p>
        <h1 className="mt-1 text-4xl font-bold">Rewards that include everyone</h1>
        <p className="mt-1 max-w-2xl text-ink-500">
          XP rewards effort, not marks. Missions are matched to each student's level, and the Class Garden grows from everyone's small steps. There is no leaderboard anywhere.
        </p>
      </div>

      {tickSuccess && (
        <div className="rounded-2xl bg-leaf-soft p-4 text-sm font-semibold text-leaf">
          ✓ {tickSuccess}
        </div>
      )}

      <div className="no-print grid gap-6 lg:grid-cols-5">
        <section className="lg:col-span-3">
          <SectionTitle title="Today's missions" hint="Toggle what the class sees. Three a day, at most." />
          <div className="space-y-3">
            {missions.length === 0 ? (
              <EmptyState
                title="No missions available"
                description="There are currently no active missions available for this class."
              />
            ) : (
              missions.map(m => {
                const on = m.is_assigned ?? true;
                return (
                  <div key={m.id} className="card flex items-center gap-4 p-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-bold">{m.title}</h3>
                        <span className="chip bg-leaf-soft text-leaf">{m.tier}</span>
                        <span className="chip bg-sage text-ink-700">
                          {m.minutes} min · {m.xp} XP
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-ink-500">{m.blurb}</p>
                    </div>
                    <button
                      role="switch"
                      aria-checked={on}
                      disabled={assignMutation.isPending}
                      onClick={() => assignMutation.mutate({ missionId: m.id, assign: !on })}
                      className={`relative h-7 w-12 rounded-full transition ${on ? "bg-leaf" : "bg-sage-2"}`}
                    >
                      <span
                        className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow transition-all ${
                          on ? "left-6" : "left-1"
                        }`}
                      />
                      <span className="sr-only">Assign {m.title}</span>
                    </button>
                  </div>
                );
              })
            )}
          </div>

          <div className="card mt-4 space-y-3 bg-sun-soft p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex-1 text-sm">
                <p className="font-bold">No device? No problem.</p>
                <p className="text-ink-700">
                  Print mission cards. Students do them on paper and you tick them off, so rewards never depend on owning a phone.
                </p>
              </div>
              <button onClick={() => window.print()} className="btn-primary">
                <Printer size={16} />
                Print cards
              </button>
            </div>

            {/* Teacher Paper Mission Tick Selector */}
            <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-sun pt-3">
              <label className="text-xs font-bold text-ink-700">Tick paper submission for:</label>
              <select
                value={selectedStudentForTick}
                onChange={e => setSelectedStudentForTick(e.target.value)}
                className="rounded-xl border border-sage-2 bg-white px-3 py-1.5 text-xs font-medium focus:outline-none"
              >
                <option value="">Select student...</option>
                {(studentsData || []).map(s => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              <button
                disabled={!selectedStudentForTick || tickMutation.isPending}
                onClick={() => {
                  if (selectedStudentForTick && missions.length > 0) {
                    tickMutation.mutate({ missionId: missions[0].id, studentId: selectedStudentForTick });
                  }
                }}
                className="btn-soft !px-3 !py-1.5 text-xs disabled:opacity-50"
              >
                <CheckSquare size={14} />
                Tick complete (+{missions[0]?.xp || 30} XP)
              </button>
            </div>
          </div>
        </section>

        <section className="lg:col-span-2">
          <SectionTitle title="Class Garden" hint={`${totalDrops} of 48 drops · ${gardenStage(pct)}`} />
          <div className="card p-4">
            <Garden pct={pct} drops={3} />
            <p className="mt-3 text-sm text-ink-500">
              Every mission adds one drop, whatever the score. Names are never shown, so nobody is singled out.
            </p>
          </div>
        </section>
      </div>

      <section className="no-print">
        <SectionTitle title="Send kudos" hint="A personal message with a badge is worth more than points." />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {eligibleKudosStudents.map((s, i) => {
            const b = BADGES[[3, 4, 0, 10, 8, 1][i % 6]];
            const sent = sentKudos.includes(s.id);
            return (
              <div key={s.id} className="card flex items-center gap-3 p-4">
                <Medal badge={b} size={52} />
                <div className="min-w-0 flex-1">
                  <p className="font-bold">{s.name}</p>
                  <p className="truncate text-xs text-ink-500">{b.name}</p>
                </div>
                <button
                  disabled={sent || kudosMutation.isPending}
                  onClick={() => kudosMutation.mutate(s.id)}
                  className="btn-soft !px-3 !py-2 disabled:opacity-60"
                >
                  {sent ? <Check size={16} /> : <Send size={16} />}
                </button>
              </div>
            );
          })}
        </div>
      </section>

      <section className="hidden print:block">
        <h2 className="mb-4 text-2xl font-bold">EduPulse mission cards · Class 9A</h2>
        <div className="grid grid-cols-2 gap-4">
          {missions
            .filter(m => m.is_assigned ?? true)
            .map(m => (
              <div key={m.id} className="rounded-2xl border-2 border-dashed border-ink-800 p-5">
                <p className="text-sm font-bold uppercase">
                  {m.tier} · {m.minutes} min · {m.xp} XP
                </p>
                <h3 className="mt-1 text-xl font-bold">{m.title}</h3>
                <p className="mt-1 text-sm">{m.blurb}</p>
                <p className="mt-6 border-t border-ink-800 pt-2 text-xs">
                  Name: ____________ Teacher tick: [&nbsp;&nbsp;&nbsp;]
                </p>
              </div>
            ))}
        </div>
      </section>
    </div>
  );
}
