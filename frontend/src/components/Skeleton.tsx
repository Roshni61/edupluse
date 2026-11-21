import React from "react";

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-2xl bg-sage-2/70 ${className}`}
    />
  );
}

export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="card space-y-3 p-5" aria-busy="true" aria-label="Loading content">
      <Skeleton className="h-6 w-1/3" />
      <Skeleton className="h-4 w-4/5" />
      {Array.from({ length: lines - 1 }).map((_, i) => (
        <Skeleton key={i} className="h-4 w-full" />
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 4, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="card space-y-3 p-5" aria-busy="true" aria-label="Loading table">
      <div className="flex gap-4 border-b border-sage-2 pb-3">
        {Array.from({ length: cols }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 py-2 border-b border-sage-2/50 last:border-0">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton key={c} className="h-8 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function MetricSkeleton() {
  return (
    <div className="card flex items-center gap-4 p-5" aria-busy="true" aria-label="Loading metric">
      <Skeleton className="h-12 w-12 rounded-2xl" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-7 w-20" />
        <Skeleton className="h-4 w-32" />
      </div>
    </div>
  );
}

export function RouteLoadingSkeleton() {
  return (
    <div className="space-y-6 py-4" aria-busy="true" aria-label="Loading page">
      <div className="space-y-2">
        <Skeleton className="h-4 w-28" />
        <Skeleton className="h-8 w-64" />
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <MetricSkeleton />
        <MetricSkeleton />
        <MetricSkeleton />
      </div>
      <CardSkeleton lines={4} />
    </div>
  );
}
