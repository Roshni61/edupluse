import React, { useState, useEffect } from "react";
import { Link, useParams, Navigate } from "react-router-dom";
import { ArrowLeft, Check, Send, TrendingDown, CalendarX, BookX, Sparkles, AlertCircle, RefreshCw } from "lucide-react";
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { teacherApi } from "../../api/client";
import { useStore } from "../../store";
import { Avatar, LevelPill } from "../../components/ui";
import { EmptyState } from "../../components/EmptyState";

interface ChartPoint {
  t: string;
  score: number;
  avg: number;
}

interface StudentDetailData {
  student: {
    id: string;
    name: string;
    class_name: string;
    subject: string;
    support_level: 1 | 2 | 3;
    attendance_pct: number;
    homework_pct: number;
    parent_who: string;
    parent_channel: string;
    reasons: string[];
    suggested_actions: string[];
  };
  tests: string[];
  class_avg: number[];
  chart_data: ChartPoint[];
  baseline: number;
  drop: number;
  reasons: string[];
  suggested_actions: string[];
  logged_actions: string[];
  parent_note_status?: string | null;
}

interface ParentNoteData {
  student_id: string;
  student_name: string;
  parent_who: string;
  channel: string;
  preferred_language: string;
  body_en: string;
  body_ta: string;
  status: string;
  sent: boolean;
}

export default function StudentDetail() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { state, dispatch } = useStore();

  const { data, isLoading, isError, error, refetch } = useQuery<StudentDetailData>({
    queryKey: ["student-detail", id],
    queryFn: () => teacherApi.getStudentDetail(id!),
    enabled: !!id,
  });

  const { data: noteData } = useQuery<ParentNoteData>({
    queryKey: ["parent-note", id],
    queryFn: () => teacherApi.getParentNote(id!),
    enabled: !!id,
  });

  const [att, setAtt] = useState<number>(90);
  const [hw, setHw] = useState<number>(90);
  const [simLevel, setSimLevel] = useState<1 | 2 | 3 | null>(null);
  const [lang, setLang] = useState<"en" | "ta">("en");
  const [note, setNote] = useState<string>("");

  useEffect(() => {
    if (data?.student) {
      setAtt(data.student.attendance_pct ?? 90);
      setHw(data.student.homework_pct ?? 90);
      setSimLevel(data.student.support_level ?? 1);
    }
  }, [data]);

  useEffect(() => {
    if (noteData) {
      setNote(lang === "en" ? noteData.body_en : noteData.body_ta);
    }
  }, [noteData, lang]);

  const whatIfMutation = useMutation({
    mutationFn: ({ attVal, hwVal }: { attVal: number; hwVal: number }) =>
      teacherApi.whatIf(id!, attVal, hwVal),
    onSuccess: res => {
      setSimLevel(res.level as 1 | 2 | 3);
    },
  });

  const handleSliderChange = (type: "att" | "hw", val: number) => {
    const newAtt = type === "att" ? val : att;
    const newHw = type === "hw" ? val : hw;
    if (type === "att") setAtt(val);
    else setHw(val);

    whatIfMutation.mutate({ attVal: newAtt, hwVal: newHw });
  };

  const logActionMutation = useMutation({
    mutationFn: (actionText: string) => teacherApi.logAction(id!, actionText),
    onSuccess: (res, actionText) => {
      dispatch({ t: "log", id: id!, action: actionText });
      queryClient.invalidateQueries({ queryKey: ["student-detail", id] });
    },
  });

  const approveNoteMutation = useMutation({
    mutationFn: () =>
      teacherApi.approveParentNote(id!, {
        body_en: lang === "en" ? note : noteData?.body_en || note,
        body_ta: lang === "ta" ? note : noteData?.body_ta || note,
        approved: true,
        channel: noteData?.channel || data?.student.parent_channel,
      }),
    onSuccess: () => {
      dispatch({ t: "note", id: id! });
      queryClient.invalidateQueries({ queryKey: ["parent-note", id] });
      queryClient.invalidateQueries({ queryKey: ["student-detail", id] });
    },
  });

  if (!id) return <Navigate to="/teacher" replace />;

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-5 w-32 rounded bg-sage-2"></div>
        <div className="card h-28 bg-white p-5"></div>
        <div className="grid gap-6 lg:grid-cols-5">
          <div className="card h-80 bg-white lg:col-span-3"></div>
          <div className="card h-80 bg-white lg:col-span-2"></div>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="card flex flex-col items-center justify-center p-8 text-center space-y-4">
        <AlertCircle size={40} className="text-coral" />
        <h2 className="text-xl font-bold">Failed to load student details</h2>
        <p className="text-sm text-ink-500 max-w-md">{(error as Error)?.message || "Student profile could not be loaded."}</p>
        <button onClick={() => refetch()} className="btn-primary !px-4 !py-2">
          <RefreshCw size={15} /> Try again
        </button>
      </div>
    );
  }

  const s = data.student;
  const base = data.baseline;
  const lvl = simLevel ?? s.support_level;
  const chartData = data.chart_data;
  const icons = [<TrendingDown key="a" size={18} />, <CalendarX key="b" size={18} />, <BookX key="c" size={18} />];
  const isSent = noteData?.sent || data.parent_note_status === "approved" || approveNoteMutation.isSuccess;
  const loggedList = data.logged_actions || [];

  return (
    <div className="space-y-6">
      <Link to="/teacher" className="inline-flex items-center gap-1.5 text-sm font-bold text-ink-700 hover:underline">
        <ArrowLeft size={16} />
        Back to today's plan
      </Link>
      <div className="card flex flex-wrap items-center gap-4 p-5">
        <Avatar name={s.name} size={64} />
        <div className="flex-1">
          <h1 className="text-3xl font-bold">{s.name}</h1>
          <p className="text-ink-500">
            {s.subject} · Class {s.class_name} · Parent: {s.parent_who} via {s.parent_channel}
          </p>
        </div>
        <LevelPill level={lvl} />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <section className="card p-5 lg:col-span-3">
          <h2 className="text-xl font-bold">{s.name} against their own usual level</h2>
          <p className="text-sm text-ink-500">
            The dashed line is {s.name}'s own baseline ({base}). Support is triggered by change from self, not by being below the class.
          </p>
          <div className="mt-4 h-64" role="img" aria-label={`Scores for ${s.name} compared with the class average and their own baseline`}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ left: -18, right: 8, top: 8 }}>
                <CartesianGrid stroke="#E4EEEA" vertical={false} />
                <XAxis dataKey="t" tick={{ fontSize: 12 }} />
                <YAxis domain={[30, 90]} tick={{ fontSize: 12 }} />
                <Tooltip />
                <ReferenceLine y={base} stroke="#0F3D3E" strokeDasharray="5 5" />
                <Line type="monotone" dataKey="avg" name="Class average" stroke="#9BB0AC" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="score" name={s.name} stroke="#FF7A59" strokeWidth={3.5} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="card p-5 lg:col-span-2">
          <h2 className="text-xl font-bold">Why this flag</h2>
          <ul className="mt-3 space-y-3">
            {data.reasons.map((r, i) => (
              <li key={r} className="flex gap-3 rounded-2xl bg-sage p-3 text-sm">
                <span className="text-coral-deep">{icons[i % 3]}</span>
                {r}
              </li>
            ))}
          </ul>
          <h3 className="mt-5 text-base font-bold">What if?</h3>
          <p className="text-xs text-ink-500">Drag to see how the support level responds.</p>
          {[
            ["Attendance", att, (v: number) => handleSliderChange("att", v)],
            ["Homework on time", hw, (v: number) => handleSliderChange("hw", v)],
          ].map(([label, v, setVal]) => (
            <label key={label as string} className="mt-3 block text-sm font-semibold">
              {label as string}: <span className="text-coral-deep">{v as number}%</span>
              <input
                type="range"
                min={40}
                max={100}
                value={v as number}
                onChange={e => (setVal as (n: number) => void)(+e.target.value)}
                className="mt-1 w-full accent-[#FF7A59]"
              />
            </label>
          ))}
          <div className="mt-4 flex items-center justify-between rounded-2xl bg-ink-800 p-3 text-white">
            <span className="text-sm">Resulting level</span>
            <LevelPill level={lvl} />
          </div>
        </section>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card p-5">
          <h2 className="text-xl font-bold">Support Playbook</h2>
          <p className="text-sm text-ink-500">Matched to the likely causes. Log what you try so we can learn what helps.</p>
          <ul className="mt-4 space-y-2">
            {data.suggested_actions.length === 0 ? (
              <EmptyState
                title="No suggested actions"
                description="No specific playbook actions are recommended at this time."
              />
            ) : (
              data.suggested_actions.map(a => {
                const done = loggedList.includes(a) || logActionMutation.isSuccess;
                return (
                  <li key={a} className="flex items-center justify-between gap-3 rounded-2xl bg-sage p-3 text-sm">
                    <span>{a}</span>
                    <button
                      disabled={done || logActionMutation.isPending}
                      onClick={() => logActionMutation.mutate(a)}
                      className={`btn !px-3 !py-1.5 ${
                        done ? "bg-leaf-soft text-leaf" : "bg-white text-ink-800 hover:bg-sun-soft"
                      }`}
                    >
                      {done ? (
                        <>
                          <Check size={14} />
                          Logged
                        </>
                      ) : (
                        "Log it"
                      )}
                    </button>
                  </li>
                );
              })
            )}
          </ul>
        </section>

        <section className="card p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Note to {s.parent_who.toLowerCase()}</h2>
            <div className="flex rounded-xl bg-sage p-1 text-xs font-bold">
              {(["en", "ta"] as const).map(l => (
                <button
                  key={l}
                  onClick={() => setLang(l)}
                  className={`rounded-lg px-3 py-1 ${lang === l ? "bg-white shadow-soft" : ""}`}
                >
                  {l === "en" ? "English" : "தமிழ்"}
                </button>
              ))}
            </div>
          </div>
          <p className="mt-1 text-sm text-ink-500">Written from facts, strengths first. Nothing is sent until you approve.</p>
          <textarea
            value={note}
            onChange={e => setNote(e.target.value)}
            rows={6}
            className="mt-3 w-full rounded-2xl border border-sage-2 bg-paper p-3 text-sm leading-relaxed focus:border-coral focus:outline-none"
            aria-label="Parent note"
          />
          <div className="mt-3 flex items-center justify-between">
            <span className="chip bg-leaf-soft text-leaf">
              <Sparkles size={13} />
              Validator passed: numbers match records
            </span>
            <button
              disabled={isSent || approveNoteMutation.isPending}
              onClick={() => approveNoteMutation.mutate()}
              className="btn-coral disabled:opacity-60"
            >
              {isSent ? (
                <>
                  <Check size={16} />
                  Approved
                </>
              ) : (
                <>
                  <Send size={16} />
                  Approve and send
                </>
              )}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
