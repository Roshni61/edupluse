import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth, Role } from "../context/AuthContext";

export function ProtectedRoute({
  allowedRoles,
  children,
}: {
  allowedRoles?: Role[];
  children: React.ReactNode;
}) {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  let effectiveUser = user;
  try {
    const saved = localStorage.getItem("edupulse_user");
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && (!effectiveUser || parsed.role !== effectiveUser.role)) {
        effectiveUser = parsed;
      }
    }
  } catch {}

  const hasToken = Boolean(localStorage.getItem("edupulse_token"));

  if (isLoading && !effectiveUser && !hasToken) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-coral border-t-transparent" />
      </div>
    );
  }

  if ((!isAuthenticated && !hasToken) || !effectiveUser) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(effectiveUser.role)) {
    // Redirect to the user's role-specific home page if they attempt cross-access
    return <Navigate to={`/${effectiveUser.role}`} replace />;
  }

  return <>{children}</>;
}
