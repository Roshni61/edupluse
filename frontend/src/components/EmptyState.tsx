import React from "react";
import { Inbox, type LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  actionText,
  onAction,
  className = "",
}: EmptyStateProps) {
  return (
    <div className={`card p-8 text-center space-y-3 ${className}`} role="status">
      <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-sage text-ink-500">
        <Icon size={24} />
      </span>
      <h3 className="text-base font-bold text-ink-900">{title}</h3>
      <p className="text-xs text-ink-500 max-w-sm mx-auto leading-relaxed">{description}</p>
      {actionText && onAction && (
        <div className="pt-2">
          <button onClick={onAction} className="btn-primary text-xs">
            {actionText}
          </button>
        </div>
      )}
    </div>
  );
}
