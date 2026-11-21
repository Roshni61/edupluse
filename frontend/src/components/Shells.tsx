import React from "react";
import { NavLink, Outlet } from "react-router-dom";
import { Home, Award, CalendarClock, PhoneCall, LayoutDashboard, Sprout, ShieldCheck, Smartphone, History } from "lucide-react";

const linkCls = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-semibold transition ${isActive ? "bg-ink-800 text-white shadow-soft" : "text-ink-700 hover:bg-sage"}`;

export function SideShell({ items, who }: { items: { to: string; label: string; icon: React.ReactNode; end?: boolean }[]; who: { name: string; sub: string } }) {
  return (
    <div className="mx-auto flex w-full max-w-[1280px] gap-6 px-4 pb-16 pt-6 lg:px-8">
      <aside className="no-print sticky top-24 hidden h-fit w-64 shrink-0 lg:block">
        <nav className="card space-y-1.5 p-3" aria-label="Section navigation">
          {items.map(i => <NavLink key={i.to} to={i.to} end={i.end} className={linkCls}>{i.icon}{i.label}</NavLink>)}
        </nav>
        <div className="card mt-4 p-4"><p className="label">Signed in as</p><p className="mt-1 font-display text-lg font-bold">{who.name}</p><p className="text-sm text-ink-500">{who.sub}</p></div>
      </aside>
      <div className="min-w-0 flex-1">
        <nav className="no-print mb-5 flex gap-2 overflow-x-auto lg:hidden" aria-label="Section navigation">
          {items.map(i => <NavLink key={i.to} to={i.to} end={i.end} className={linkCls}>{i.icon}{i.label}</NavLink>)}
        </nav>
        <Outlet />
      </div>
    </div>
  );
}
export const TeacherShell = () => (
  <SideShell who={{ name: "Ms. Priya", sub: "Class 9A · Maths" }} items={[
    { to: "/teacher", label: "Today", icon: <LayoutDashboard size={18} />, end: true },
    { to: "/teacher/connect", label: "Parent Connect", icon: <CalendarClock size={18} /> },
    { to: "/teacher/missions", label: "Missions and Garden", icon: <Sprout size={18} /> },
  ]} />
);
export const AdminShell = () => (
  <SideShell
    who={{ name: "Mr. Raghavan", sub: "Principal" }}
    items={[
      { to: "/admin", label: "School overview", icon: <ShieldCheck size={18} />, end: true },
      { to: "/admin/audit-logs", label: "Audit logs", icon: <History size={18} /> },
    ]}
  />
);

export function PhoneShell({ items, tint }: { items: { to: string; label: string; icon: React.ReactNode; end?: boolean }[]; tint: string }) {
  return (
    <div className="grid place-items-center px-3 pb-6 pt-4 lg:pt-8">
      <div className={`relative flex h-[calc(100dvh-9.5rem)] min-h-[560px] w-full max-w-[440px] flex-col overflow-hidden rounded-[2.2rem] border border-sage-2 shadow-soft sm:h-[calc(100dvh-7rem)] lg:h-[800px] ${tint}`}>
        <div className="flex-1 overflow-y-auto px-5 pb-28 pt-6"><Outlet /></div>
        <nav aria-label="Primary" className="no-print absolute inset-x-3 bottom-3 flex justify-around rounded-3xl border border-sage-2 bg-white/95 p-2 shadow-soft backdrop-blur">
          {items.map(i => (
            <NavLink key={i.to} to={i.to} end={i.end} className={({ isActive }) => `flex flex-1 flex-col items-center gap-1 rounded-2xl py-2 text-[11px] font-bold ${isActive ? "bg-ink-800 text-white" : "text-ink-500"}`}>{i.icon}{i.label}</NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}
export const StudentShell = () => <PhoneShell tint="bg-[#F3F8F6]" items={[{ to: "/student", label: "Home", icon: <Home size={20} />, end: true }, { to: "/student/badges", label: "Badges", icon: <Award size={20} /> }]} />;
export const ParentShell = () => <PhoneShell tint="bg-[#FFF8F4]" items={[
  { to: "/parent", label: "Home", icon: <Home size={20} />, end: true },
  { to: "/parent/book", label: "Book a call", icon: <PhoneCall size={20} /> },
  { to: "/parent/reach", label: "Reach me", icon: <Smartphone size={20} /> },
]} />;
