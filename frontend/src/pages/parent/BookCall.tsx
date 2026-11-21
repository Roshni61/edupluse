import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Download, Phone, Mic, Video, School, AlertCircle } from "lucide-react";
import { DAYS, WINDOWS } from "../../types";
import { useStore } from "../../store";
import { useT } from "../../i18n";
import { parentApi } from "../../api/client";

export default function BookCall() {
  const t = useT();
  const { dispatch } = useStore();
  const queryClient = useQueryClient();

  const [day, setDay] = useState("Mon");
  const [win, setWin] = useState("am");
  const [slot, setSlot] = useState<string | null>(null);
  const [method, setMethod] = useState("call");
  const [rem, setRem] = useState<string[]>(["whatsapp", "hour"]);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [done, setDone] = useState<{ id: string; day: string; time: string; label: string } | null>(null);

  const { data: slotsData } = useQuery({
    queryKey: ["parent-slots"],
    queryFn: () => parentApi.getSlots(),
  });

  const windowsList = slotsData?.windows || WINDOWS;
  const daysList = slotsData?.days || DAYS.filter((d) => d !== "Sat");
  const bookedSlots = slotsData?.booked || {};

  const methods = [
    { id: "call", label: t("teacherCalls"), icon: <Phone size={18} /> },
    { id: "voice", label: t("voiceNotes"), icon: <Mic size={18} /> },
    { id: "video", label: t("video"), icon: <Video size={18} /> },
    { id: "visit", label: t("visit"), icon: <School size={18} /> },
  ];

  const w = windowsList.find((x: any) => x.id === win) || windowsList[0];
  const allowed = (wid: string, d: string) => {
    const targetWin = windowsList.find((x: any) => x.id === wid);
    if (!targetWin) return false;
    return !(d === "Sat") && !(targetWin.extended && d !== "Tue" && d !== "Thu");
  };

  const needsSlot = method === "call" || method === "video";
  const ok = needsSlot ? Boolean(slot && allowed(win, day)) : true;
  const toggle = (k: string) =>
    setRem((r) => (r.includes(k) ? r.filter((x) => x !== k) : [...r, k]));

  const bookMutation = useMutation({
    mutationFn: async (payload: { day: string; window_id: string; time: string; method: string; reminders: string[] }) => {
      setBookingError(null);
      return parentApi.bookCall(payload);
    },
    onSuccess: (res, vars) => {
      queryClient.invalidateQueries({ queryKey: ["parent-slots"] });
      queryClient.invalidateQueries({ queryKey: ["parent-home"] });
      const label = methods.find((m) => m.id === vars.method)?.label || vars.method;
      dispatch({
        t: "book",
        b: {
          id: res.id,
          day: res.day,
          time: res.time,
          method: label,
          reminders: rem,
        },
      });
      setDone({ id: res.id, day: res.day, time: res.time, label });
    },
    onError: (err: any) => {
      setBookingError(err.message || "Failed to book call. Please try another slot.");
    },
  });

  const confirm = () => {
    const time = method === "visit" ? "10:00 AM" : method === "voice" ? "Anytime" : slot!;
    const dd = method === "visit" ? "Sat" : method === "voice" ? "Any day" : day;
    bookMutation.mutate({
      day: dd,
      window_id: win,
      time,
      method,
      reminders: rem,
    });
  };

  const ics = async () => {
    if (!done) return;
    try {
      await parentApi.downloadIcs(done.id);
    } catch {
      // Fallback: client generation
      const body = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//EduPulse//Parent Connect//EN",
        "BEGIN:VEVENT",
        `UID:${done.id}@edupulse.demo`,
        `DTSTART:${Date.now()}`,
        "SUMMARY:5-minute check-in with child's class teacher",
        "DESCRIPTION:Short call about child's week. The teacher will call you.",
        "BEGIN:VALARM",
        "TRIGGER:-PT1H",
        "ACTION:DISPLAY",
        "DESCRIPTION:Call in 1 hour",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR",
      ].join("\r\n");
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([body], { type: "text/calendar" }));
      a.download = "edupulse-call.ics";
      a.click();
    }
  };

  if (done)
    return (
      <div className="space-y-5 pt-6 text-center">
        <span className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-leaf text-white">
          <Check size={32} />
        </span>
        <h1 className="text-3xl font-bold">You're booked</h1>
        <div className="card p-5 text-left">
          <p className="font-bold">
            {done.day} · {done.time}
          </p>
          <p className="text-sm text-ink-500">{done.label}</p>
          <p className="mt-3 text-sm">
            Reminders:{" "}
            {rem.length
              ? rem
                  .map(
                    (r) =>
                      (
                        {
                          whatsapp: "WhatsApp",
                          sms: "SMS",
                          cal: "Calendar",
                          day: "1 day before",
                          hour: "1 hour before",
                          five: "5 minutes before",
                        } as Record<string, string>
                      )[r]
                  )
                  .join(", ")
              : "none"}
          </p>
        </div>
        <p className="text-sm text-ink-500">
          It's only five minutes. The teacher will call you, so you don't need to install anything.
        </p>
        <button onClick={ics} className="btn-primary w-full">
          <Download size={16} />
          Add to my calendar (.ics)
        </button>
      </div>
    );

  return (
    <div className="space-y-5">
      <header>
        <p className="label">5 minutes, your time</p>
        <h1 className="mt-1 text-2xl font-bold">{t("book")}</h1>
      </header>

      {bookingError && (
        <div className="card flex items-center gap-3 border-coral bg-coral-soft p-4 text-coral-deep text-sm font-semibold">
          <AlertCircle size={20} className="shrink-0" />
          <p>{bookingError}</p>
        </div>
      )}

      <section>
        <p className="label mb-2">How</p>
        <div className="grid gap-2">
          {methods.map((m) => (
            <button
              key={m.id}
              onClick={() => {
                setMethod(m.id);
                setBookingError(null);
              }}
              aria-pressed={method === m.id}
              className={`flex items-center gap-3 rounded-2xl border-2 p-3.5 text-left text-sm font-bold ${
                method === m.id ? "border-ink-800 bg-white" : "border-transparent bg-white/70"
              }`}
            >
              <span className="text-coral-deep">{m.icon}</span>
              {m.label}
            </button>
          ))}
        </div>
      </section>

      {needsSlot && (
        <>
          <section>
            <p className="label mb-2">Day</p>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {daysList.map((d: string) => (
                <button
                  key={d}
                  onClick={() => {
                    setDay(d);
                    setSlot(null);
                    setBookingError(null);
                  }}
                  aria-pressed={day === d}
                  className={`rounded-2xl px-4 py-2.5 text-sm font-bold ${
                    day === d ? "bg-ink-800 text-white" : "bg-white"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </section>

          <section>
            <p className="label mb-2">When suits you?</p>
            <div className="grid gap-2">
              {windowsList.map((x: any) => {
                const off = !allowed(x.id, day);
                const isBooked = Boolean(bookedSlots[`${day}-${x.id}`]);
                return (
                  <button
                    key={x.id}
                    disabled={off}
                    onClick={() => {
                      setWin(x.id);
                      setSlot(null);
                      setBookingError(null);
                    }}
                    aria-pressed={win === x.id}
                    className={`rounded-2xl border-2 p-3 text-left ${
                      win === x.id ? "border-ink-800 bg-white" : "border-transparent bg-white/70"
                    } disabled:opacity-40`}
                  >
                    <div className="flex justify-between items-center">
                      <p className="text-sm font-bold">{x.label}</p>
                      {isBooked && !off && (
                        <span className="text-xs text-coral-deep font-semibold">1 slot booked</span>
                      )}
                    </div>
                    <p className="text-xs text-ink-500">
                      {off ? "Not offered on this day" : x.time}
                    </p>
                  </button>
                );
              })}
            </div>

            {allowed(win, day) && (
              <div className="mt-3 grid grid-cols-3 gap-2">
                {w.slots.map((s: string) => (
                  <button
                    key={s}
                    onClick={() => {
                      setSlot(s);
                      setBookingError(null);
                    }}
                    aria-pressed={slot === s}
                    className={`rounded-xl py-2.5 text-sm font-bold ${
                      slot === s ? "bg-coral text-ink-900 shadow-pop" : "bg-white"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            <p className="mt-2 text-xs text-ink-500">
              Can only talk later in the evening? Choose "voice notes" above and reply whenever you're free.
            </p>
          </section>
        </>
      )}

      <section>
        <p className="label mb-2">{t("reminders")}</p>
        <div className="flex flex-wrap gap-2">
          {[
            ["whatsapp", "WhatsApp"],
            ["sms", "SMS"],
            ["cal", "Calendar"],
            ["day", "1 day before"],
            ["hour", "1 hour before"],
            ["five", "5 min before"],
          ].map(([k, l]) => (
            <button
              key={k}
              onClick={() => toggle(k)}
              aria-pressed={rem.includes(k)}
              className={`chip !px-3.5 !py-2 text-xs ${
                rem.includes(k) ? "bg-ink-800 text-white" : "bg-white text-ink-700"
              }`}
            >
              {l}
            </button>
          ))}
        </div>
      </section>

      <button
        disabled={!ok || bookMutation.isPending}
        onClick={confirm}
        className="btn-coral w-full disabled:opacity-40"
      >
        {bookMutation.isPending ? "Booking..." : t("confirm")}
      </button>
    </div>
  );
}
