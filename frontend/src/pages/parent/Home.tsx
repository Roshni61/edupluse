import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Smile,
  Meh,
  Frown,
  Mic,
  Send,
  CalendarClock,
  Check,
  Square,
  Phone,
  MessageCircle,
} from "lucide-react";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { parentApi } from "../../api/client";

export default function ParentHome() {
  const t = useT();
  const { state, dispatch } = useStore();
  const queryClient = useQueryClient();

  const [mood, setMood] = useState<string | null>(null);
  const [rec, setRec] = useState(false);
  const [secs, setSecs] = useState(0);
  const [voice, setVoice] = useState(false);

  React.useEffect(() => {
    if (!rec) return;
    const id = setInterval(() => setSecs((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [rec]);

  const { data, isLoading } = useQuery({
    queryKey: ["parent-home"],
    queryFn: parentApi.getHome,
  });

  const checkinMutation = useMutation({
    mutationFn: (vars: { mood: string; voice: boolean }) =>
      parentApi.checkin({ mood: vars.mood, has_voice_note: vars.voice }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["parent-home"] });
      dispatch({ t: "checkin", mood: mood!, voice });
    },
  });

  const moods = [
    { id: "great", icon: <Smile size={28} />, label: t("great"), tone: "bg-leaf-soft text-leaf" },
    { id: "okay", icon: <Meh size={28} />, label: t("okay"), tone: "bg-sun-soft text-[#9A6B00]" },
    { id: "hard", icon: <Frown size={28} />, label: t("hard"), tone: "bg-coral-soft text-coral-deep" },
  ];

  const child = data?.child;
  const note = data?.latest_note;
  const next = data?.next_booking || state.bookings[state.bookings.length - 1];
  const isCheckedIn = Boolean(data?.recent_checkin || state.checkin || checkinMutation.isSuccess);
  const shiftWorker = data?.preferences?.shift_worker ?? false;

  const handleSendCheckin = () => {
    if (!mood) return;
    checkinMutation.mutate({ mood, voice });
  };

  return (
    <div className="space-y-5">
      <header>
        <p className="label">{t("glance")}</p>
        <h1 className="mt-1 text-2xl font-bold leading-snug">
          {t("hello")}
        </h1>
      </header>

      {shiftWorker && (
        <aside className="rounded-2xl border border-coral/30 bg-coral-soft p-4 text-xs font-semibold text-coral-deep flex items-center gap-3">
          <MessageCircle size={20} className="shrink-0" />
          <div>
            <p className="font-bold">Shift-worker schedule active</p>
            <p className="mt-0.5 text-ink-700 font-normal">
              You can exchange voice notes anytime. No need to schedule during school hours if your shift conflicts.
            </p>
          </div>
        </aside>
      )}

      <section className="card space-y-4 p-5">
        <div>
          <p className="label !text-leaf">{t("well")}</p>
          <p className="mt-1.5 leading-relaxed">
            {child?.growth_highlight || t("wellText")}
          </p>
        </div>

        <div className="rounded-2xl bg-sage p-3.5 text-sm leading-relaxed text-ink-700">
          {note?.body || t("summary")}
        </div>

        <div className="rounded-2xl bg-sun-soft p-3.5">
          <p className="label !text-[#9A6B00]">{t("tryHome")}</p>
          <p className="mt-1.5 text-sm leading-relaxed">{t("tryText")}</p>
        </div>
      </section>

      <section className="card p-5">
        <h2 className="text-lg font-bold">{t("checkin")}</h2>
        <p className="text-sm text-ink-500">{t("checkinQ")}</p>
        {isCheckedIn ? (
          <p className="mt-4 flex items-center gap-2 rounded-2xl bg-leaf-soft p-3 text-sm font-semibold text-leaf">
            <Check size={18} />
            {t("thanks")}
          </p>
        ) : (
          <>
            <div className="mt-3 grid grid-cols-3 gap-2.5" role="radiogroup" aria-label={t("checkinQ")}>
              {moods.map((m) => (
                <button
                  key={m.id}
                  role="radio"
                  aria-checked={mood === m.id}
                  onClick={() => setMood(m.id)}
                  className={`flex flex-col items-center gap-1.5 rounded-2xl border-2 p-3 text-sm font-bold transition ${
                    mood === m.id ? "border-ink-800 " + m.tone : "border-transparent bg-sage text-ink-700"
                  }`}
                >
                  {m.icon}
                  {m.label}
                </button>
              ))}
            </div>
            <div className="mt-3 flex items-center gap-2.5">
              <button
                onClick={() => {
                  if (rec) {
                    setRec(false);
                    setVoice(true);
                  } else {
                    setSecs(0);
                    setRec(true);
                    setVoice(false);
                  }
                }}
                className={`btn flex-1 ${rec ? "bg-coral text-ink-900" : "bg-sage text-ink-800"}`}
                aria-pressed={rec}
              >
                {rec ? (
                  <>
                    <Square size={16} />0:{String(secs).padStart(2, "0")}
                  </>
                ) : voice ? (
                  <>
                    <Check size={16} />
                    {t("voice")} ✓
                  </>
                ) : (
                  <>
                    <Mic size={16} />
                    {t("voice")}
                  </>
                )}
              </button>
              <button
                disabled={!mood || checkinMutation.isPending}
                onClick={handleSendCheckin}
                className="btn-primary flex-1 disabled:opacity-40"
              >
                <Send size={16} />
                {checkinMutation.isPending ? "Sending..." : t("send")}
              </button>
            </div>
          </>
        )}
      </section>

      <section className="card p-5">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-coral-soft text-coral-deep">
            <CalendarClock size={22} />
          </span>
          <div className="flex-1">
            <p className="label">{t("nextCall")}</p>
            <p className="font-bold">
              {next ? `${next.day} · ${next.time} · ${next.method}` : "Not booked yet"}
            </p>
          </div>
        </div>
        <Link to="/parent/book" className="btn-coral mt-4 w-full">
          {t("book")}
        </Link>
        <Link to="/parent/reach" className="btn-soft mt-2 w-full">
          <Phone size={16} />
          {t("noPhone")}
        </Link>
      </section>
    </div>
  );
}
