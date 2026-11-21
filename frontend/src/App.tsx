import React, { Suspense } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { RotateCcw, LogOut, LogIn, UserCheck } from "lucide-react";
import { useStore } from "./store";
import { useAuth, Role } from "./context/AuthContext";
import { Logo } from "./components/ui";
import { Celebrate, Toast } from "./components/Celebrate";
import { AdminShell, ParentShell, StudentShell, TeacherShell } from "./components/Shells";
import { ProtectedRoute } from "./components/RouteGuard";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { RouteLoadingSkeleton } from "./components/Skeleton";

// Lazy-load route chunks for fast 3G loading and small bundle sizes
const Landing = React.lazy(() => import("./pages/Landing"));
const Login = React.lazy(() => import("./pages/Login"));
const Dashboard = React.lazy(() => import("./pages/teacher/Dashboard"));
const StudentDetail = React.lazy(() => import("./pages/teacher/StudentDetail"));
const ParentConnect = React.lazy(() => import("./pages/teacher/ParentConnect"));
const Missions = React.lazy(() => import("./pages/teacher/Missions"));
const StudentHome = React.lazy(() => import("./pages/student/Home"));
const MissionPlay = React.lazy(() => import("./pages/student/MissionPlay"));
const Badges = React.lazy(() => import("./pages/student/Badges"));
const ParentHome = React.lazy(() => import("./pages/parent/Home"));
const BookCall = React.lazy(() => import("./pages/parent/BookCall"));
const Reach = React.lazy(() => import("./pages/parent/Reach"));
const Overview = React.lazy(() => import("./pages/admin/Overview"));
const AuditLogs = React.lazy(() => import("./pages/admin/AuditLogs"));

const ROLES: { id: Role; label: string }[] = [
  { id: "teacher", label: "Teacher" },
  { id: "student", label: "Student" },
  { id: "parent", label: "Parent" },
  { id: "admin", label: "Admin" },
];

const isDemoMode = import.meta.env.VITE_DEMO_MODE !== "false";

function TopBar() {
  const { pathname } = useLocation();
  const nav = useNavigate();
  const { state, dispatch } = useStore();
  const { user, isAuthenticated, logout, resetDemo, quickLogin } = useAuth();
  const role = pathname.split("/")[1];

  const handleRoleSwitch = async (rId: Role) => {
    if (isDemoMode && (!isAuthenticated || user?.role !== rId)) {
      try {
        await quickLogin(rId);
        nav("/" + rId);
      } catch {
        nav("/login");
      }
    } else {
      nav("/" + rId);
    }
  };

  const handleResetDemo = async () => {
    try {
      await resetDemo();
      dispatch({ t: "reset" });
      dispatch({ t: "toast", v: "Demo data reset to clean seeded state!" });
      nav("/");
    } catch (e: any) {
      dispatch({ t: "toast", v: "Reset demo failed: " + (e.message || "Unknown error") });
    }
  };

  const handleLogout = async () => {
    await logout();
    nav("/login");
  };

  return (
    <header className="no-print sticky top-0 z-40 border-b border-sage-2 bg-white/85 backdrop-blur">
      <div className="mx-auto flex max-w-[1280px] flex-wrap items-center gap-3 px-4 py-3 lg:px-8">
        <Link to="/" aria-label="EduPulse home">
          <Logo />
        </Link>
        <span className="chip hidden bg-sun-soft text-[#9A6B00] sm:inline-flex">
          {isDemoMode ? "Prototype · Seeded Demo" : "Production"}
        </span>

        {/* User indicator when authenticated */}
        {isAuthenticated && user && (
          <span className="hidden items-center gap-1.5 rounded-full border border-sage-2 bg-white px-3 py-1 text-xs font-bold text-ink-700 md:inline-flex">
            <UserCheck size={14} className="text-coral" />
            {user.name} ({user.role})
          </span>
        )}

        <div className="ml-auto flex flex-wrap items-center gap-2">
          {/* Role switcher */}
          <div className="flex rounded-2xl bg-sage p-1" role="tablist" aria-label="Switch role">
            {ROLES.map((r) => (
              <button
                key={r.id}
                role="tab"
                aria-selected={role === r.id || user?.role === r.id}
                onClick={() => handleRoleSwitch(r.id)}
                className={`rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                  (user ? user.role === r.id : role === r.id)
                    ? "bg-ink-800 text-white shadow-soft"
                    : "text-ink-700 hover:bg-white"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          {/* Language selection (EN / TA) */}
          <div className="flex rounded-2xl bg-sage p-1" aria-label="Language selection">
            {(["en", "ta"] as const).map((l) => (
              <button
                key={l}
                onClick={() => dispatch({ t: "lang", v: l })}
                aria-pressed={state.lang === l}
                className={`rounded-xl px-3 py-1.5 text-xs font-semibold ${
                  state.lang === l ? "bg-white text-ink-800 shadow-soft" : "text-ink-500"
                }`}
              >
                {l === "en" ? "EN" : "தமிழ்"}
              </button>
            ))}
          </div>

          {/* Reset demo button: ONLY when VITE_DEMO_MODE=true */}
          {isDemoMode && (
            <button
              className="btn-soft !px-3 !py-2 text-xs"
              onClick={handleResetDemo}
              title="Reset demo (calls backend /demo/reset)"
            >
              <RotateCcw size={15} />
              <span className="hidden lg:inline">Reset demo</span>
            </button>
          )}

          {/* Login or Logout Button */}
          {isAuthenticated ? (
            <button
              className="btn-soft !px-3 !py-2 text-xs text-ink-700 hover:text-red-600"
              onClick={handleLogout}
              title="Sign out"
            >
              <LogOut size={15} />
              <span className="hidden md:inline">Log out</span>
            </button>
          ) : (
            <Link to="/login" className="btn-coral !px-3.5 !py-2 text-xs font-bold" title="Sign in">
              <LogIn size={15} />
              <span>Sign in</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen">
      <TopBar />
      <ErrorBoundary>
        <Suspense fallback={<div className="mx-auto max-w-[1280px] p-6"><RouteLoadingSkeleton /></div>}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />

            {/* Teacher portal with ProtectedRoute */}
            <Route
              path="/teacher"
              element={
                <ProtectedRoute allowedRoles={["teacher"]}>
                  <TeacherShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="student/:id" element={<StudentDetail />} />
              <Route path="connect" element={<ParentConnect />} />
              <Route path="missions" element={<Missions />} />
            </Route>

            {/* Student portal with ProtectedRoute */}
            <Route
              path="/student"
              element={
                <ProtectedRoute allowedRoles={["student"]}>
                  <StudentShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<StudentHome />} />
              <Route path="play/:id" element={<MissionPlay />} />
              <Route path="badges" element={<Badges />} />
            </Route>

            {/* Parent portal with ProtectedRoute */}
            <Route
              path="/parent"
              element={
                <ProtectedRoute allowedRoles={["parent"]}>
                  <ParentShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<ParentHome />} />
              <Route path="book" element={<BookCall />} />
              <Route path="reach" element={<Reach />} />
            </Route>

            {/* Admin portal with ProtectedRoute */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={["admin"]}>
                  <AdminShell />
                </ProtectedRoute>
              }
            >
              <Route index element={<Overview />} />
              <Route path="audit-logs" element={<AuditLogs />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
      <Celebrate />
      <Toast />
    </div>
  );
}
