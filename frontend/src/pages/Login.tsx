import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Lock, Mail, ArrowRight, GraduationCap, Sparkles, Users, ShieldCheck, AlertCircle } from "lucide-react";
import { useAuth, Role, DEMO_CREDENTIALS } from "../context/AuthContext";
import { useStore } from "../store";
import { useT } from "../i18n";
import { Logo } from "../components/ui";

const isDemoMode = import.meta.env.VITE_DEMO_MODE === "true" || import.meta.env.DEV;

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, quickLogin, isLoading: authLoading } = useAuth();
  const { state, dispatch } = useStore();
  const t = useT();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const from = (location.state as any)?.from?.pathname;

  const handleRedirect = (role: Role) => {
    if (from && from.startsWith(`/${role}`)) {
      navigate(from, { replace: true });
    } else {
      navigate(`/${role}`, { replace: true });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const user = await login(email, password);
      handleRedirect(user.role);
    } catch (err: any) {
      setError(err.message || "Invalid email or password");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = async (role: Role) => {
    setError(null);
    setIsSubmitting(true);
    try {
      const user = await quickLogin(role);
      handleRedirect(user.role);
    } catch (err: any) {
      setError(err.message || "Quick login failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-[calc(100vh-80px)] max-w-4xl flex-col justify-center px-4 py-12">
      <div className="mx-auto w-full max-w-md">
        {/* Header & Logo */}
        <div className="text-center">
          <div className="inline-block"><Logo /></div>
          <h1 className="mt-4 font-display text-3xl font-bold tracking-tight">{t("signIn")}</h1>
          <p className="mt-2 text-sm text-ink-500">{t("signInDesc")}</p>
        </div>

        {/* Language switcher */}
        <div className="mt-4 flex justify-center">
          <div className="flex rounded-2xl bg-sage p-1" aria-label="Language selection">
            {(["en", "ta"] as const).map(l => (
              <button
                key={l}
                type="button"
                onClick={() => dispatch({ t: "lang", v: l })}
                aria-pressed={state.lang === l}
                className={`rounded-xl px-3.5 py-1 text-xs font-bold transition ${
                  state.lang === l ? "bg-white text-ink-800 shadow-soft" : "text-ink-500 hover:text-ink-800"
                }`}
              >
                {l === "en" ? "English" : "தமிழ்"}
              </button>
            ))}
          </div>
        </div>

        {/* Login Card */}
        <div className="card mt-6 p-7 shadow-soft">
          {error && (
            <div className="mb-5 flex items-start gap-2.5 rounded-2xl border border-red-200 bg-red-50 p-3.5 text-sm text-red-700">
              <AlertCircle size={18} className="mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label" htmlFor="email">
                {t("emailLabel")}
              </label>
              <div className="relative mt-1">
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="teacher@edupulse.demo"
                  className="w-full rounded-2xl border border-sage-2 bg-white px-4 py-2.5 pl-10 text-sm font-medium outline-none transition focus:border-ink-800 focus:ring-2 focus:ring-ink-800/10"
                />
                <Mail size={16} className="absolute left-3.5 top-3.5 text-ink-500" />
              </div>
            </div>

            <div>
              <label className="label" htmlFor="password">
                {t("passwordLabel")}
              </label>
              <div className="relative mt-1">
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-2xl border border-sage-2 bg-white px-4 py-2.5 pl-10 text-sm font-medium outline-none transition focus:border-ink-800 focus:ring-2 focus:ring-ink-800/10"
                />
                <Lock size={16} className="absolute left-3.5 top-3.5 text-ink-500" />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || authLoading}
              className="btn-coral w-full !py-3 text-center font-bold disabled:opacity-50"
            >
              {isSubmitting ? t("signingIn") : t("signInBtn")}
            </button>
          </form>
        </div>

        {/* Demo Quick-Login Options (when VITE_DEMO_MODE=true) */}
        {isDemoMode && (
          <div className="mt-8">
            <div className="relative flex py-2 items-center">
              <div className="flex-grow border-t border-sage-2"></div>
              <span className="flex-shrink mx-4 text-xs font-bold uppercase tracking-wider text-ink-500">
                {t("quickDemoHeading")}
              </span>
              <div className="flex-grow border-t border-sage-2"></div>
            </div>
            <p className="text-center text-xs text-ink-500">{t("quickDemoSub")}</p>

            <div className="mt-4 grid grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => handleQuickLogin("teacher")}
                disabled={isSubmitting}
                className="flex items-center gap-2 rounded-2xl bg-ink-800 p-3 text-left text-white shadow-soft transition hover:-translate-y-0.5 hover:bg-ink-700 disabled:opacity-50"
              >
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-white/20">
                  <GraduationCap size={16} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold leading-tight">{t("demoTeacher")}</p>
                  <p className="truncate text-[10px] text-white/70">Class 9A</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin("student")}
                disabled={isSubmitting}
                className="flex items-center gap-2 rounded-2xl bg-coral-soft p-3 text-left text-ink-800 shadow-soft transition hover:-translate-y-0.5 hover:bg-[#FCD8CF] disabled:opacity-50"
              >
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-coral/20 text-coral">
                  <Sparkles size={16} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold leading-tight">{t("demoStudent")}</p>
                  <p className="truncate text-[10px] text-ink-500">Growth View</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin("parent")}
                disabled={isSubmitting}
                className="flex items-center gap-2 rounded-2xl bg-sun-soft p-3 text-left text-ink-800 shadow-soft transition hover:-translate-y-0.5 hover:bg-[#FFEFC7] disabled:opacity-50"
              >
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-[#E09D00]/20 text-[#A87200]">
                  <Users size={16} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold leading-tight">{t("demoParent")}</p>
                  <p className="truncate text-[10px] text-ink-500">Karthik's Mom</p>
                </div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin("admin")}
                disabled={isSubmitting}
                className="flex items-center gap-2 rounded-2xl bg-sky-soft p-3 text-left text-ink-800 shadow-soft transition hover:-translate-y-0.5 hover:bg-[#D5EBF9] disabled:opacity-50"
              >
                <div className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-[#0284C7]/20 text-[#0369A1]">
                  <ShieldCheck size={16} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold leading-tight">{t("demoAdmin")}</p>
                  <p className="truncate text-[10px] text-ink-500">School HM</p>
                </div>
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
