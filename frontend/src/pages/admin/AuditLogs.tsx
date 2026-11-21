import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Shield, Filter, Search, ChevronLeft, ChevronRight, Activity } from "lucide-react";
import { adminApi } from "../../api/client";
import { SectionTitle } from "../../components/ui";
import { EmptyState } from "../../components/EmptyState";

export default function AuditLogs() {
  const [actionFilter, setActionFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = 15;

  const { data, isLoading } = useQuery({
    queryKey: ["admin-audit-logs", actionFilter, roleFilter, page],
    queryFn: () =>
      adminApi.getAuditLogs({
        action: actionFilter || undefined,
        actor_role: roleFilter || undefined,
        limit: pageSize,
        offset: page * pageSize,
      }),
  });

  const total = data?.total ?? 0;
  const items = data?.items ?? [];
  const maxPages = Math.ceil(total / pageSize);

  const formatTime = (ts: string) => {
    try {
      const d = new Date(ts);
      return d.toLocaleString("en-IN", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch {
      return ts;
    }
  };

  const badgeColor = (action: string) => {
    if (action.includes("VIOLATION")) return "bg-coral-soft text-coral-deep border border-coral";
    if (action.includes("UPDATE") || action.includes("TICK")) return "bg-sun-soft text-[#9A6B00]";
    return "bg-sage text-ink-700";
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link to="/admin" className="inline-flex items-center gap-1.5 text-xs font-bold text-ink-500 hover:text-ink-800">
            <ArrowLeft size={14} /> Back to School Overview
          </Link>
          <h1 className="mt-1 text-3xl font-bold">Audit Logs</h1>
          <p className="mt-1 text-sm text-ink-500">
            PRODUCT RULE 7: Every sensitive read and write by teacher or admin is written to an immutable audit log.
          </p>
        </div>
      </div>

      <div className="card flex flex-wrap items-center gap-3 p-4">
        <div className="flex flex-1 items-center gap-2 rounded-xl bg-sage px-3 py-2 text-sm text-ink-700 min-w-[200px]">
          <Search size={16} className="text-ink-500" />
          <input
            type="text"
            placeholder="Filter by action (e.g. VIEW, UPDATE)..."
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(0);
            }}
            className="w-full bg-transparent outline-none placeholder:text-ink-400 text-sm"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter size={16} className="text-ink-500" />
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(0);
            }}
            className="rounded-xl border border-sage-2 bg-white px-3 py-2 text-xs font-bold text-ink-700 outline-none"
          >
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="teacher">Teacher</option>
            <option value="parent">Parent</option>
          </select>
        </div>
      </div>

      <div className="card overflow-x-auto p-4">
        <table className="w-full min-w-[700px] text-sm">
          <thead>
            <tr className="border-b border-sage-2 text-left">
              <th className="p-3"><span className="label">Timestamp</span></th>
              <th className="p-3"><span className="label">Actor</span></th>
              <th className="p-3"><span className="label">Action</span></th>
              <th className="p-3"><span className="label">Resource</span></th>
              <th className="p-3"><span className="label">Details</span></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={5} className="p-6 text-center text-ink-500">
                  Loading audit log records...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-4">
                  <EmptyState
                    title="No audit logs found"
                    description="No recorded activity matches your current filter criteria."
                  />
                </td>
              </tr>
            ) : (
              items.map((log: any) => (
                <tr key={log.id} className="border-b border-sage-2 hover:bg-sage/40 transition">
                  <td className="p-3 text-xs text-ink-500 whitespace-nowrap">{formatTime(log.created_at)}</td>
                  <td className="p-3">
                    <span className="font-bold text-xs uppercase px-2 py-0.5 rounded-md bg-ink-800 text-white">
                      {log.actor_role}
                    </span>
                    <p className="text-[11px] text-ink-400 font-mono mt-0.5">{log.actor_id.slice(0, 8)}...</p>
                  </td>
                  <td className="p-3">
                    <span className={`inline-block px-2.5 py-1 rounded-xl text-xs font-bold ${badgeColor(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="p-3 text-xs font-semibold text-ink-700">
                    {log.entity} {log.entity_id ? `(${log.entity_id.slice(0, 8)})` : ""}
                  </td>
                  <td className="p-3 text-xs text-ink-500 font-mono max-w-[280px] truncate" title={JSON.stringify(log.meta)}>
                    {JSON.stringify(log.meta)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        <div className="mt-4 flex items-center justify-between border-t border-sage-2 pt-3 text-xs text-ink-500">
          <span>
            Showing {items.length} of {total} records
          </span>
          <div className="flex items-center gap-2">
            <button
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              className="btn-soft !px-2.5 !py-1.5 disabled:opacity-30"
              aria-label="Previous page"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="font-bold">
              Page {page + 1} of {Math.max(1, maxPages)}
            </span>
            <button
              disabled={page + 1 >= maxPages}
              onClick={() => setPage((p) => p + 1)}
              className="btn-soft !px-2.5 !py-1.5 disabled:opacity-30"
              aria-label="Next page"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
