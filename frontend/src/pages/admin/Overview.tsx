import React from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Lock,
  ShieldCheck,
  Users,
  Smile,
  PhoneCall,
  History,
  AlertTriangle,
} from "lucide-react";
import { SectionTitle } from "../../components/ui";
import { adminApi } from "../../api/client";

const DEFAULT_EQUITY = [{ band: "Needs support", earned: 74 }, { band: "On track", earned: 81 }, { band: "Strong", earned: 85 }];
const DEFAULT_HEAT = [
  [1, 1, 2, 2, 1, 1], [2, 2, 3, 3, 2, 2], [1, 2, 2, 2, 1, 1], [3, 2, 2, 1, 1, 1], [1, 1, 1, 2, 2, 1], [2, 2, 2, 3, 2, 2],
];
const DEFAULT_HEAT_CLASSES = ["8A", "8B", "9A", "9B", "10A", "10B"];
const DEFAULT_REACH = [{ name: "App or WhatsApp", value: 58 }, { name: "SMS", value: 18 }, { name: "Voice call", value: 12 }, { name: "Callback or in person", value: 12 }];

const heatColors = [
  "bg-leaf-soft text-leaf",
  "bg-sun-soft text-[#9A6B00]",
  "bg-coral-soft text-coral-deep",
];
const pieColors = ["#0F3D3E", "#2E8B7A", "#F4B942", "#FF7A59"];

export default function Overview() {
  const { data: overviewData } = useQuery({
    queryKey: ["admin-overview"],
    queryFn: adminApi.getOverview,
  });

  const { data: guardrailsData } = useQuery({
    queryKey: ["admin-guardrails"],
    queryFn: adminApi.getGuardrails,
  });

  const kpisData = overviewData?.kpis;
  const kpis = [
    {
      icon: <Users size={20} />,
      v: kpisData ? kpisData.support_plan_count.toString() : "212",
      l: "Students with a support plan",
      tone: "bg-coral-soft text-coral-deep",
    },
    {
      icon: <PhoneCall size={20} />,
      v: kpisData ? `${kpisData.families_reached_pct}%` : "88%",
      l: "Families reached this week",
      tone: "bg-leaf-soft text-leaf",
    },
    {
      icon: <Smile size={20} />,
      v: kpisData ? `${kpisData.badge_earning_pct}%` : "81%",
      l: "Students earned a badge this month",
      tone: "bg-sun-soft text-[#9A6B00]",
    },
  ];

  const equityList = overviewData?.equity || DEFAULT_EQUITY;
  const reachList = overviewData?.reach || DEFAULT_REACH;
  const heatClasses = overviewData?.heat_classes || DEFAULT_HEAT_CLASSES;
  const heatMatrix = overviewData?.heat || DEFAULT_HEAT;
  const alert = overviewData?.equity_alert;

  const guardrailsList =
    guardrailsData?.guardrails || [
      { key: "1", label: "Public leaderboards", value: "Off, locked", locked: true },
      { key: "2", label: "Push notifications to children", value: "Off, locked", locked: true },
      { key: "3", label: "Daily mission cap", value: "3 per student", locked: false },
      { key: "4", label: "Student view (rewards and missions)", value: "On, school can switch off", locked: false },
      { key: "5", label: "Sensitive attributes used by the model", value: "None, locked", locked: true },
      { key: "6", label: "Fairness alert threshold", value: "10 points gap", locked: false },
    ];

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="label">School overview</p>
          <h1 className="mt-1 text-4xl font-bold">Are we helping everyone, fairly?</h1>
          <p className="mt-1 max-w-2xl text-ink-500">
            Aggregated views only. No individual child's data is shown to admins.
          </p>
        </div>
        <Link to="/admin/audit-logs" className="btn-soft inline-flex items-center gap-2">
          <History size={16} />
          View audit logs
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {kpis.map((k) => (
          <div key={k.l} className="card flex items-center gap-4 p-5">
            <span className={`grid h-12 w-12 place-items-center rounded-2xl ${k.tone}`}>{k.icon}</span>
            <div>
              <p className="font-display text-3xl font-bold">{k.v}</p>
              <p className="text-sm text-ink-500">{k.l}</p>
            </div>
          </div>
        ))}
      </div>

      {alert && alert.flagged && (
        <div className="rounded-2xl border-2 border-coral bg-coral-soft p-4 flex items-start gap-3">
          <AlertTriangle className="text-coral-deep shrink-0 mt-0.5" size={22} />
          <div>
            <h3 className="font-bold text-coral-deep text-base">Equity Alert</h3>
            <p className="mt-0.5 text-sm font-medium text-ink-800">{alert.message}</p>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <section className="card p-5 lg:col-span-3">
          <h2 className="text-xl font-bold">Engagement equity</h2>
          <p className="text-sm text-ink-500">
            Share of students who earned at least one badge this month, by performance band. A big gap would mean the
            rewards favour the top.
          </p>
          <div className="mt-4 h-60" role="img" aria-label="Badge earning rate by performance band">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={equityList} margin={{ left: -12, top: 8 }}>
                <CartesianGrid vertical={false} stroke="#E4EEEA" />
                <XAxis dataKey="band" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} unit="%" />
                <Tooltip formatter={(v: number) => `${v}%`} />
                <Bar dataKey="earned" name="Earned a badge" radius={[10, 10, 0, 0]}>
                  {equityList.map((_: any, i: number) => (
                    <Cell key={i} fill={["#FF7A59", "#2E8B7A", "#0F3D3E"][i % 3]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 rounded-2xl bg-sage p-3 text-sm text-ink-700">
            {alert ? alert.message : "Gap between bands within fairness threshold."}
          </p>
        </section>

        <section className="card p-5 lg:col-span-2">
          <h2 className="text-xl font-bold">How families are reached</h2>
          <div className="h-52" role="img" aria-label="Share of families by channel">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={reachList} dataKey="value" innerRadius={48} outerRadius={80} paddingAngle={3}>
                  {reachList.map((_: any, i: number) => (
                    <Cell key={i} fill={pieColors[i % pieColors.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: number) => `${v}%`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <ul className="space-y-1.5 text-sm">
            {reachList.map((r: any, i: number) => (
              <li key={r.name} className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ background: pieColors[i % pieColors.length] }} />
                {r.name}
                <b className="ml-auto">{r.value}%</b>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="card p-5">
        <SectionTitle
          title="Support levels by class, last 6 weeks"
          hint="Darker means more students needing support. Used to plan where extra help goes."
        />
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <thead>
              <tr>
                <th className="p-2 text-left">
                  <span className="label">Class</span>
                </th>
                {[1, 2, 3, 4, 5, 6].map((w) => (
                  <th key={w} className="p-2">
                    <span className="label">Wk {w}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {heatMatrix.map((row: number[], r: number) => (
                <tr key={r}>
                  <td className="p-2 font-bold">{heatClasses[r] || `Class ${r + 1}`}</td>
                  {row.map((v: number, c: number) => (
                    <td key={c} className="p-1.5">
                      <div className={`rounded-xl py-3 text-center text-xs font-bold ${heatColors[v - 1]}`}>
                        {["Low", "Medium", "High"][v - 1]}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <SectionTitle title="Guardrails" hint="Responsible-design settings the school controls." />
        <div className="grid gap-3 md:grid-cols-2">
          {guardrailsList.map((g: any) => (
            <div key={g.key || g.label} className="card flex items-center gap-3 p-4">
              {g.locked ? (
                <Lock size={18} className="text-coral-deep shrink-0" />
              ) : (
                <ShieldCheck size={18} className="text-leaf shrink-0" />
              )}
              <div className="flex-1">
                <p className="font-bold">{g.label}</p>
                <p className="text-sm text-ink-500">{g.value}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
