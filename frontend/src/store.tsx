import React, { createContext, useContext, useEffect, useReducer } from "react";

export type Lang = "en" | "ta";

export interface Booking {
  id: string;
  day: string;
  time: string;
  method: string;
  reminders: string[];
}

export interface State {
  lang: Lang;
  toast: string | null;
  unlock: string | null;
  budget: number;
  lowTech: boolean;
  // Ephemeral in-memory UI helpers
  bookings: Booking[];
  callbacks: string[];
  checkin: { mood: string; voice: boolean } | null;
}

export const INITIAL: State = {
  lang: "en",
  toast: null,
  unlock: null,
  budget: 20,
  lowTech: false,
  bookings: [],
  callbacks: [],
  checkin: null,
};

export type Action =
  | { t: "lang"; v: Lang }
  | { t: "toast"; v: string | null }
  | { t: "unlock"; v: string }
  | { t: "clearUnlock" }
  | { t: "budget"; v: number }
  | { t: "lowTech"; v: boolean }
  | { t: "checkin"; mood: string; voice: boolean }
  | { t: "book"; b: Booking }
  | { t: "callback"; id: string }
  | { t: "reset" }
  // Compatibility actions for any remaining calls
  | { t: "mission"; id: string; xp: number; badge?: string }
  | { t: "note"; id: string }
  | { t: "log"; id: string; action: string }
  | { t: "kudos"; id: string }
  | { t: "assign"; id: string };

function reducer(s: State, a: Action): State {
  switch (a.t) {
    case "lang":
      return { ...s, lang: a.v };
    case "toast":
      return { ...s, toast: a.v };
    case "unlock":
      return { ...s, unlock: a.v };
    case "clearUnlock":
      return { ...s, unlock: null };
    case "budget":
      return { ...s, budget: a.v };
    case "lowTech":
      return { ...s, lowTech: a.v };
    case "checkin":
      return { ...s, checkin: { mood: a.mood, voice: a.voice }, toast: "Thanks! Your check-in reached the teacher." };
    case "book":
      return { ...s, bookings: [...s.bookings, a.b] };
    case "callback":
      return { ...s, callbacks: [...s.callbacks, a.id], toast: "Callback slot reserved and family notified." };
    case "reset":
      return { ...INITIAL, lang: s.lang };
    case "mission":
      return a.badge ? { ...s, unlock: a.badge } : s;
    case "note":
      return { ...s, toast: "Approved and queued to send in the parent's preferred channel." };
    case "log":
      return { ...s, toast: "Action logged. We'll compare progress in 4 to 6 weeks." };
    case "kudos":
      return { ...s, toast: "Kudos sent. It appears on the student's home screen." };
    case "assign":
      return s;
    default:
      return s;
  }
}

const LANG_KEY = "edupulse_lang";

function loadLang(): Lang {
  try {
    const raw = localStorage.getItem(LANG_KEY);
    if (raw === "en" || raw === "ta") return raw;
  } catch {
    /* storage unavailable */
  }
  return "en";
}

const Ctx = createContext<{ state: State; dispatch: React.Dispatch<Action> } | null>(null);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, { ...INITIAL, lang: loadLang() });

  // Only language preference is stored in localStorage
  useEffect(() => {
    try {
      localStorage.setItem(LANG_KEY, state.lang);
    } catch {
      /* ignore */
    }
  }, [state.lang]);

  // Toast auto-clear
  useEffect(() => {
    if (state.toast) {
      const id = setTimeout(() => dispatch({ t: "toast", v: null }), 3200);
      return () => clearTimeout(id);
    }
  }, [state.toast]);

  return <Ctx.Provider value={{ state, dispatch }}>{children}</Ctx.Provider>;
}

export function useStore() {
  const c = useContext(Ctx);
  if (!c) throw new Error("StoreProvider missing");
  return c;
}
