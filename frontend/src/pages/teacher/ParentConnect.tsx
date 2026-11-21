import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { CalendarClock, Mic, Phone, MessageSquareText, Info, Check, Wand2 } from "lucide-react";
import { DAYS, LADDER, WINDOWS } from "../../types";

const DEFAULT_BOOKED: Record<string, string> = { "Mon-am": "Meena's mother", "Tue-lunch": "Arun's grandmother", "Wed-pm": "Vikram's mother", "Thu-eve": "Rahul's father" };
const DEFAULT_UNREACHED = [
  { id: "u1", who: "Divya's father", why: "Night-shift worker. Two missed calls.", suggest: "Voice note, reply when free" },
  { id: "u2", who: "Arun's grandmother", why: "Feature phone. Tamil voice call not answered twice.", suggest: "Saturday school desk or a neighbour contact" },
  { id: "u3", who: "Vikram's mother", why: "No reply to the weekly summary for 2 weeks.", suggest: "SMS with reply codes, then a callback" },
];
import { useStore } from "../../store";
import { SectionTitle } from "../../components/ui";
import { teacherApi } from "../../api/client";

const icon = (id: string) =>
  id === "u1" ? <Mic size={18} /> : id === "u2" ? <Phone size={18} /> : <MessageSquareText size={18} />;

export default function ParentConnect() {
  const { state, dispatch } = useStore();
  const queryClient = useQueryClient();

  const { data: connectData, isLoading } = useQuery({
    queryKey: ["teacher-connect"],
    queryFn: teacherApi.getConnect,
  });

  const reserveMutation = useMutation({
    mutationFn: (callbackId: string) =>
      teacherApi.reserveCallback({
        callback_id: callbackId,
        day: "Tue",
        time: "1:00 PM",
        method: "call",
      }),
    onSuccess: (res, callbackId) => {
      queryClient.invalidateQueries({ queryKey: ["teacher-connect"] });
      dispatch({ t: "callback", id: callbackId });
      dispatch({ t: "toast", v: "Callback reserved and family notified via WhatsApp/SMS." });
    },
  });

  const ladderList = connectData?.ladder || LADDER;
  const unreachedList = connectData?.unreached || DEFAULT_UNREACHED;

  const serverBooked = connectData?.booked || {};
  const booked = {
    ...DEFAULT_BOOKED,
    ...serverBooked,
    ...Object.fromEntries(state.bookings.map((b) => [`${b.day}-${windowOf(b.time)}`, "Karthik's mother"])),
  };

  const count = Object.keys(booked).length;

  return (
    <div className="space-y-8">
      <div>
        <p className="label">Parent Connect</p>
        <h1 className="mt-1 text-4xl font-bold">Every family, reached in a way that works</h1>
        <p className="mt-1 max-w-2xl text-ink-500">
          Five-minute calls inside your real working hours, and a ladder that moves from app to SMS to voice call to a
          person, so nobody is left out.
        </p>
      </div>

      <section>
        <SectionTitle
          title="The reach ladder"
          hint="EduPulse starts at the family's preferred step and only moves down if there's no acknowledgement in 48 hours."
        />
        <div className="grid gap-3 md:grid-cols-5">
          {ladderList.map((l: any) => (
            <div key={l.step} className="card p-4">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-ink-800 font-display font-bold text-white">
                {l.step}
              </span>
              <h3 className="mt-3 text-base font-bold leading-tight">{l.name}</h3>
              <p className="mt-1 text-xs text-ink-500">{l.desc}</p>
              <p className="mt-3 font-display text-2xl font-bold text-coral-deep">
                {l.count}
                <span className="ml-1 text-xs font-sans font-semibold text-ink-500">families</span>
              </p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <SectionTitle
          title="Needs a human touch"
          hint="Not reached for two weeks. A kind, specific next step is suggested for each."
        />
        <div className="space-y-3">
          {unreachedList.map((u: any) => {
            const done = state.callbacks.includes(u.id) || u.status === "reserved";
            return (
              <div key={u.id} className="card flex flex-wrap items-center gap-4 p-4">
                <span className="grid h-11 w-11 place-items-center rounded-2xl bg-coral-soft text-coral-deep">
                  {icon(u.id)}
                </span>
                <div className="min-w-0 flex-1">
                  <h3 className="font-bold">{u.who}</h3>
                  <p className="text-sm text-ink-500">{u.why}</p>
                  <p className="mt-0.5 text-sm font-semibold text-ink-700">Try: {u.suggest}</p>
                </div>
                <button
                  disabled={done || reserveMutation.isPending}
                  onClick={() => reserveMutation.mutate(u.id)}
                  className={done ? "btn bg-leaf-soft text-leaf" : "btn-primary"}
                >
                  {done ? (
                    <>
                      <Check size={16} />
                      Booked
                    </>
                  ) : reserveMutation.isPending ? (
                    "Booking..."
                  ) : (
                    "Reserve callback"
                  )}
                </button>
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <SectionTitle
          title="This week's five-minute calls"
          hint={`${count} booked · budget 8 calls (40 minutes). Windows sit inside school hours.`}
          right={
            <button
              onClick={() => dispatch({ t: "toast", v: "Auto-fit placed 3 pending requests into the best open slots." })}
              className="btn-soft"
            >
              <Wand2 size={16} />
              Auto-fit requests
            </button>
          }
        />
        <div className="card overflow-x-auto p-4">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr>
                <th className="p-2 text-left">
                  <span className="label">Window</span>
                </th>
                {DAYS.map((d) => (
                  <th key={d} className="p-2 text-center">
                    <span className="label">{d}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {WINDOWS.map((w) => (
                <tr key={w.id} className="border-t border-sage-2">
                  <td className="p-2">
                    <p className="font-bold">{w.label}</p>
                    <p className="text-xs text-ink-500">{w.time}</p>
                  </td>
                  {DAYS.map((d) => {
                    const off = d === "Sat" || (w.extended && d !== "Tue" && d !== "Thu");
                    const who = booked[`${d}-${w.id}`];
                    return (
                      <td key={d} className="p-1.5 text-center">
                        {off ? (
                          <span className="block rounded-xl bg-paper py-3 text-xs text-ink-500/60">
                            {d === "Sat" ? "School desk" : "Closed"}
                          </span>
                        ) : who ? (
                          <span className="block rounded-xl bg-coral-soft px-1 py-3 text-xs font-bold text-coral-deep">
                            {who}
                          </span>
                        ) : (
                          <span className="block rounded-xl bg-leaf-soft py-3 text-xs font-bold text-leaf">Open</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 flex items-start gap-2 text-sm text-ink-500">
          <Info size={16} className="mt-0.5 shrink-0" />
          Evening slots are limited to Tuesday and Thursday to protect your time. Families who can only talk later get a
          voice-note exchange instead, which you answer when it suits you.
        </p>
      </section>
    </div>
  );
}

function windowOf(time: string) {
  const w = WINDOWS.find((x) => x.slots.includes(time));
  return w ? w.id : "am";
}
