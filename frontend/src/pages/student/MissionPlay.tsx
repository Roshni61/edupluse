import React, { useState } from "react";
import { useNavigate, useParams, Navigate } from "react-router-dom";
import { ArrowLeft, Lightbulb, PartyPopper } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { studentApi } from "../../api/client";
import { MISSIONS } from "../../types";
import { useStore } from "../../store";

const QS = [
  {
    q: "Which fraction is bigger?",
    opts: ["1/2", "3/4", "They are equal"],
    a: 1,
    hint: "Think of two pizzas. Cut one into 2 slices and one into 4. Which slice is more?",
  },
  {
    q: "What is 2/5 of 10?",
    opts: ["2", "4", "5"],
    a: 1,
    hint: "Split 10 into 5 equal parts first. How big is one part?",
  },
  {
    q: "Simplify 6/8",
    opts: ["2/3", "3/4", "6/4"],
    a: 1,
    hint: "What number goes into both 6 and 8?",
  },
];

export default function MissionPlay() {
  const { id } = useParams();
  const nav = useNavigate();
  const { dispatch } = useStore();
  const queryClient = useQueryClient();

  const m = MISSIONS.find(x => x.id === id);
  const [i, setI] = useState(0);
  const [pick, setPick] = useState<number | null>(null);
  const [tries, setTries] = useState(0);
  const [totalHints, setTotalHints] = useState(0);
  const [finished, setFinished] = useState(false);
  const [earnedXp, setEarnedXp] = useState(m?.xp || 30);

  const submitMutation = useMutation({
    mutationFn: () =>
      studentApi.submitMission(m!.id, { hints_used: totalHints, tries: tries + 1, score: 100 }),
    onSuccess: res => {
      setEarnedXp(res.xp_awarded);
      dispatch({ t: "mission", id: m!.id, xp: res.xp_awarded, badge: res.badge_unlocked || undefined });
      queryClient.invalidateQueries({ queryKey: ["student-home"] });
      queryClient.invalidateQueries({ queryKey: ["student-badges"] });
      queryClient.invalidateQueries({ queryKey: ["class-garden"] });
      setFinished(true);
    },
    onError: () => {
      // Offline fallback
      dispatch({ t: "mission", id: m!.id, xp: m!.xp, badge: m!.badge });
      setFinished(true);
    },
  });

  if (!m) return <Navigate to="/student" replace />;

  const finish = () => {
    submitMutation.mutate();
  };

  if (finished) {
    return (
      <div className="grid place-items-center pt-10 text-center">
        <PartyPopper size={54} className="text-coral" />
        <h1 className="mt-4 text-3xl font-bold">Mission done!</h1>
        <p className="mt-2 text-ink-500">+{earnedXp} XP and one more drop for the Class Garden.</p>
        <button className="btn-coral mt-6" onClick={() => nav("/student")}>
          Back home
        </button>
      </div>
    );
  }

  if (m.kind !== "quiz") {
    return (
      <div className="space-y-5">
        <button onClick={() => nav("/student")} className="inline-flex items-center gap-1.5 text-sm font-bold">
          <ArrowLeft size={16} />
          Back
        </button>
        <h1 className="text-3xl font-bold">{m.title}</h1>
        <p className="card p-5 text-ink-700">{m.blurb}</p>
        <button
          disabled={submitMutation.isPending}
          onClick={finish}
          className="btn-coral w-full"
        >
          {submitMutation.isPending
            ? "Submitting..."
            : m.kind === "help"
            ? "I explained it to a friend"
            : "I asked my doubt"}
        </button>
      </div>
    );
  }

  const q = QS[i];
  const right = pick === q.a;

  return (
    <div className="space-y-5">
      <button onClick={() => nav("/student")} className="inline-flex items-center gap-1.5 text-sm font-bold">
        <ArrowLeft size={16} />
        Back
      </button>
      <div className="flex gap-1.5" aria-label={`Question ${i + 1} of ${QS.length}`}>
        {QS.map((_, k) => (
          <span key={k} className={`h-2 flex-1 rounded-full ${k <= i ? "bg-coral" : "bg-sage-2"}`} />
        ))}
      </div>
      <h1 className="text-3xl font-bold">{q.q}</h1>
      <div className="space-y-2.5">
        {q.opts.map((o, k) => (
          <button
            key={o}
            onClick={() => {
              setPick(k);
              if (k !== q.a) {
                setTries(t => t + 1);
                setTotalHints(h => h + 1);
              }
            }}
            disabled={right}
            className={`w-full rounded-2xl border-2 p-4 text-left text-lg font-bold transition ${
              pick === k
                ? k === q.a
                  ? "border-leaf bg-leaf-soft"
                  : "border-sun bg-sun-soft"
                : "border-sage-2 bg-white hover:border-coral"
            }`}
          >
            {o}
          </button>
        ))}
      </div>

      {pick !== null && !right && (
        <div className="card flex gap-3 bg-sun-soft p-4 text-sm" role="status">
          <Lightbulb className="shrink-0 text-[#9A6B00]" size={20} />
          <p>
            <b>Not yet, and that's fine.</b> {q.hint} Try again, no marks lost.
          </p>
        </div>
      )}

      {right && (
        <div className="card bg-leaf-soft p-4 text-sm font-semibold" role="status">
          {tries > 0 ? "You tried again and got it. That's a real skill." : "Nice work."}
        </div>
      )}

      {right && (
        <button
          disabled={submitMutation.isPending}
          className="btn-coral w-full"
          onClick={() => {
            if (i + 1 < QS.length) {
              setI(i + 1);
              setPick(null);
              setTries(0);
            } else {
              finish();
            }
          }}
        >
          {submitMutation.isPending
            ? "Submitting..."
            : i + 1 < QS.length
            ? "Next question"
            : "Finish mission"}
        </button>
      )}
    </div>
  );
}
