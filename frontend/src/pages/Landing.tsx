import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, GraduationCap, Users, ShieldCheck, Sparkles, LogIn, KeyRound } from "lucide-react";
import { Pulse } from "../components/ui";
import { useAuth, Role } from "../context/AuthContext";

const isDemoMode = import.meta.env.VITE_DEMO_MODE === "true" || import.meta.env.DEV;

const roles = [
  { role: "teacher" as Role, to: "/teacher", icon: <GraduationCap />, title: "Teacher", text: "A daily list that fits your 20 minutes, reasons in plain words, and parent calls booked for you.", tone: "bg-ink-800 text-white", sub: "text-white/75" },
  { role: "student" as Role, to: "/student", icon: <Sparkles />, title: "Student", text: "Missions, medals and a Class Garden that grows together. Progress against your own past.", tone: "bg-coral-soft text-ink-800", sub: "text-ink-700" },
  { role: "parent" as Role, to: "/parent", icon: <Users />, title: "Parent", text: "A weekly note in Tamil or English, a 3-tap check-in, and 5-minute calls that fit your day.", tone: "bg-sun-soft text-ink-800", sub: "text-ink-700" },
  { role: "admin" as Role, to: "/admin", icon: <ShieldCheck />, title: "Admin", text: "School-wide view with an engagement equity check, so rewards never favour only the top.", tone: "bg-sky-soft text-ink-800", sub: "text-ink-700" },
];

export default function Landing() {
  const navigate = useNavigate();
  const { user, isAuthenticated, quickLogin } = useAuth();
  const [loggingInRole, setLoggingInRole] = useState<string | null>(null);

  const handleQuickLogin = async (role: Role) => {
    setLoggingInRole(role);
    try {
      const loggedUser = await quickLogin(role);
      navigate(`/${loggedUser.role}`);
    } catch (e) {
      console.error("Quick login failed:", e);
      navigate("/login");
    } finally {
      setLoggingInRole(null);
    }
  };

  return (
    <main>
      <section className="relative overflow-hidden bg-ink-800 text-white">
        <Pulse className="-right-24 top-1/2 hidden h-[560px] w-[560px] -translate-y-1/2 md:block" />
        <div className="mx-auto max-w-[1280px] px-4 py-16 lg:px-8 lg:py-24">
          <p className="label !text-coral">Prasunex Innovathon 2026 · Round 3 prototype</p>
          <h1 className="mt-4 max-w-3xl text-5xl font-bold leading-[1.05] !text-white md:text-6xl">Notice early. Motivate every child. Reach every parent.</h1>
          <p className="mt-6 max-w-2xl text-lg text-white/80">EduPulse helps schools spot a struggling student weeks earlier, then keeps that student, their classmates and their family engaged in ways that work in real life, including for families without smartphones.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            {isAuthenticated && user ? (
              <Link to={`/${user.role}`} className="btn-coral">
                Continue as {user.name} ({user.role}) <ArrowRight size={18} />
              </Link>
            ) : (
              <>
                <Link to="/login" className="btn-coral">
                  Sign in to Portal <LogIn size={18} />
                </Link>
                {isDemoMode && (
                  <button
                    onClick={() => handleQuickLogin("teacher")}
                    disabled={!!loggingInRole}
                    className="btn bg-white/10 text-white hover:bg-white/20"
                  >
                    {loggingInRole === "teacher" ? "Signing in..." : "Demo Teacher Login"}
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </section>

      {/* Demo Quick-Login Banner on Landing Page (When VITE_DEMO_MODE=true) */}
      {isDemoMode && (
        <section className="border-b border-sage-2 bg-sage/60 py-6">
          <div className="mx-auto max-w-[1280px] px-4 lg:px-8">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <span className="chip bg-coral/10 text-coral font-bold inline-flex items-center gap-1.5">
                  <KeyRound size={14} /> Quick Demo Access
                </span>
                <h2 className="mt-1 text-lg font-bold">1-Click Login with Seeded Demo Accounts</h2>
                <p className="text-xs text-ink-500">Sign in instantly as any role to test role scoping and ownership guards.</p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickLogin("teacher")}
                  disabled={!!loggingInRole}
                  className="rounded-2xl bg-ink-800 px-3.5 py-2 text-xs font-bold text-white shadow-soft transition hover:bg-ink-700 disabled:opacity-50"
                >
                  {loggingInRole === "teacher" ? "Signing in..." : "Teacher (Ms. Priya)"}
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin("student")}
                  disabled={!!loggingInRole}
                  className="rounded-2xl bg-coral px-3.5 py-2 text-xs font-bold text-white shadow-soft transition hover:bg-coral/90 disabled:opacity-50"
                >
                  {loggingInRole === "student" ? "Signing in..." : "Student (Karthik)"}
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin("parent")}
                  disabled={!!loggingInRole}
                  className="rounded-2xl bg-[#E09D00] px-3.5 py-2 text-xs font-bold text-white shadow-soft transition hover:bg-[#C98B00] disabled:opacity-50"
                >
                  {loggingInRole === "parent" ? "Signing in..." : "Parent (Mother)"}
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin("admin")}
                  disabled={!!loggingInRole}
                  className="rounded-2xl bg-[#0284C7] px-3.5 py-2 text-xs font-bold text-white shadow-soft transition hover:bg-[#0369A1] disabled:opacity-50"
                >
                  {loggingInRole === "admin" ? "Signing in..." : "Admin (Principal)"}
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      <section className="mx-auto max-w-[1280px] px-4 py-12 lg:px-8">
        <h2 className="text-3xl font-bold">Pick who you want to be</h2>
        <p className="mt-1 text-ink-500">
          {isAuthenticated
            ? `Signed in as ${user?.name} (${user?.role}). Click below to visit portals.`
            : "Select a portal to view. Protected routes will prompt for authentication."}
        </p>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {roles.map(r => (
            <div
              key={r.to}
              onClick={() => {
                if (!isAuthenticated && isDemoMode) {
                  handleQuickLogin(r.role);
                } else {
                  navigate(r.to);
                }
              }}
              className={`group cursor-pointer rounded-3xl p-6 shadow-soft transition hover:-translate-y-1 ${r.tone}`}
            >
              <div className="grid h-12 w-12 place-items-center rounded-2xl bg-white/20 [&>svg]:h-6 [&>svg]:w-6">{r.icon}</div>
              <h3 className={`mt-5 text-2xl font-bold ${r.tone.includes("text-white") ? "!text-white" : ""}`}>{r.title}</h3>
              <p className={`mt-2 text-sm leading-relaxed ${r.sub}`}>{r.text}</p>
              <span className="mt-5 inline-flex items-center gap-1.5 text-sm font-bold">
                {isAuthenticated && user?.role === r.role ? "Open your portal" : "Open portal"}{" "}
                <ArrowRight size={16} className="transition group-hover:translate-x-1" />
              </span>
            </div>
          ))}
        </div>

        <div className="card mt-10 grid gap-6 p-7 md:grid-cols-3">
          {[["Fair rewards", "XP rewards effort, so a student who finds maths hard earns the same as one who finds it easy. No public leaderboards."],
          ["Works without a smartphone", "A five-step reach ladder: app, SMS, voice call, teacher callback, school desk. Nobody is left out."],
          ["Short, respectful calls", "Five-minute slots inside the teacher's real working hours, with reminders and a voice-note option for shift workers."]].map(([t, d]) => (
            <div key={t}><h3 className="text-lg font-bold">{t}</h3><p className="mt-1 text-sm text-ink-500">{d}</p></div>
          ))}
        </div>
      </section>
    </main>
  );
}
