import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import { StoreProvider } from "./store";
import { AuthProvider } from "./context/AuthContext";
import { ErrorBoundary } from "./components/ErrorBoundary";
import "./index.css";

const CACHE_KEY = "edupulse_query_cache";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60 * 5, // 5 minutes stale time for smooth 3G performance
      gcTime: 1000 * 60 * 60 * 24, // 24 hours retention
      networkMode: "offlineFirst", // Show cached data immediately when offline or slow connection
    },
  },
});

// Restore query cache from localStorage on startup (offline persistence)
try {
  const cached = localStorage.getItem(CACHE_KEY);
  if (cached) {
    const parsed = JSON.parse(cached);
    if (parsed && typeof parsed === "object") {
      Object.entries(parsed).forEach(([key, val]: [string, any]) => {
        try {
          const queryKey = JSON.parse(key);
          if (val && val.data !== undefined) {
            queryClient.setQueryData(queryKey, val.data);
          }
        } catch {
          /* ignore invalid entry */
        }
      });
    }
  }
} catch {
  /* localStorage unavailable */
}

// Persist query cache updates to localStorage (debounced)
let saveTimeout: any = null;
queryClient.getQueryCache().subscribe((event) => {
  if (event.type === "updated" || event.type === "added") {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(() => {
      try {
        const cacheObj: Record<string, any> = {};
        queryClient
          .getQueryCache()
          .getAll()
          .forEach((query) => {
            if (query.state.data !== undefined && query.state.status === "success") {
              cacheObj[JSON.stringify(query.queryKey)] = {
                data: query.state.data,
                dataUpdatedAt: query.state.dataUpdatedAt,
              };
            }
          });
        localStorage.setItem(CACHE_KEY, JSON.stringify(cacheObj));
      } catch {
        /* ignore storage quota exceeded */
      }
    }, 1000);
  }
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <HashRouter>
          <StoreProvider>
            <AuthProvider>
              <App />
            </AuthProvider>
          </StoreProvider>
        </HashRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
