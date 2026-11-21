/**
 * EduPulse Frontend API Client.
 * Handles fetch requests, automatic Bearer token injection, and automatic token refresh on 401.
 */

import { API_BASE_URL } from "../config";

const API_BASE = API_BASE_URL.endsWith("/api/v1") ? API_BASE_URL : `${API_BASE_URL}/api/v1`;

interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
}

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem("edupulse_refresh_token");
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) {
      localStorage.removeItem("edupulse_token");
      localStorage.removeItem("edupulse_refresh_token");
      localStorage.removeItem("edupulse_user");
      return null;
    }

    const data = await res.json();
    localStorage.setItem("edupulse_token", data.access_token);
    if (data.refresh_token) {
      localStorage.setItem("edupulse_refresh_token", data.refresh_token);
    }
    return data.access_token;
  } catch {
    return null;
  }
}

export async function apiFetch<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!options.skipAuth) {
    const token = localStorage.getItem("edupulse_token");
    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let res = await fetch(url, { ...options, headers });

  // Handle 401 Unauthorized with token refresh
  if (res.status === 401 && !options.skipAuth) {
    if (!isRefreshing) {
      isRefreshing = true;
      const newToken = await refreshAccessToken();
      isRefreshing = false;

      if (newToken) {
        onRefreshed(newToken);
        headers.set("Authorization", `Bearer ${newToken}`);
        res = await fetch(url, { ...options, headers });
      } else {
        window.location.hash = "#/login";
        throw new Error("Session expired. Please log in again.");
      }
    } else {
      // Wait for existing refresh to complete
      const retryToken = await new Promise<string>(resolve => {
        refreshSubscribers.push(resolve);
      });
      headers.set("Authorization", `Bearer ${retryToken}`);
      res = await fetch(url, { ...options, headers });
    }
  }

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      // Non-json error
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

// =========================================================================
// TEACHER API METHODS
// =========================================================================

export const teacherApi = {
  getTodayPlan: (budget: number = 20) =>
    apiFetch(`/teacher/today?budget=${budget}`),

  getStudents: (params?: { class_name?: string; level?: number; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.class_name) q.set("class_name", params.class_name);
    if (params?.level) q.set("level", params.level.toString());
    if (params?.search) q.set("search", params.search);
    return apiFetch(`/teacher/students?${q.toString()}`);
  },

  getStudentDetail: (studentId: string) =>
    apiFetch(`/teacher/students/${studentId}`),

  whatIf: (studentId: string, attendance: number, homework: number) =>
    apiFetch(`/teacher/students/${studentId}/what-if`, {
      method: "POST",
      body: JSON.stringify({ attendance, homework }),
    }),

  getActions: (studentId: string) =>
    apiFetch(`/teacher/students/${studentId}/actions`),

  logAction: (studentId: string, action: string, note?: string) =>
    apiFetch(`/teacher/students/${studentId}/actions`, {
      method: "POST",
      body: JSON.stringify({ action, note }),
    }),

  getParentNote: (studentId: string) =>
    apiFetch(`/teacher/students/${studentId}/parent-note`),

  approveParentNote: (
    studentId: string,
    payload: { body_en: string; body_ta?: string; approved?: boolean; channel?: string }
  ) =>
    apiFetch(`/teacher/students/${studentId}/parent-note`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getBrightSpots: () =>
    apiFetch("/teacher/bright-spots"),

  sendKudos: (studentId: string, message?: string) =>
    apiFetch("/teacher/kudos", {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, message }),
    }),

  getMissions: () =>
    apiFetch("/teacher/missions"),

  assignMission: (missionId: string, assign: boolean) =>
    apiFetch("/teacher/missions", {
      method: "POST",
      body: JSON.stringify({ mission_id: missionId, assign }),
    }),

  tickMission: (missionId: string, studentId: string, note?: string) =>
    apiFetch(`/teacher/missions/${missionId}/tick`, {
      method: "POST",
      body: JSON.stringify({ student_id: studentId, note }),
    }),

  getPrintCards: () =>
    apiFetch("/teacher/print-cards"),

  getDoubts: () =>
    apiFetch("/teacher/doubts"),

  getConnect: () =>
    apiFetch("/teacher/connect"),

  reserveCallback: (payload: { callback_id: string; day?: string; time?: string; method?: string }) =>
    apiFetch("/teacher/callbacks", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

// =========================================================================
// STUDENT API METHODS
// =========================================================================

export const studentApi = {
  getHome: () =>
    apiFetch("/student/home"),

  startMission: (missionId: string) =>
    apiFetch(`/student/missions/${missionId}/start`, { method: "POST" }),

  submitMission: (
    missionId: string,
    payload: { hints_used?: number; tries?: number; score?: number }
  ) =>
    apiFetch(`/student/missions/${missionId}/submit`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  postDoubt: (payload: { text: string; topic?: string }) =>
    apiFetch("/student/doubts", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getBadges: () =>
    apiFetch("/student/badges"),
};

// =========================================================================
// PARENT API METHODS
// =========================================================================

export const parentApi = {
  getHome: () =>
    apiFetch("/parent/home"),

  checkin: (payload: { mood: string; has_voice_note?: boolean; voice_note_url?: string }) =>
    apiFetch("/parent/checkins", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  uploadVoiceCheckin: async (mood: string, file: Blob) => {
    const token = localStorage.getItem("edupulse_token");
    const formData = new FormData();
    formData.append("mood", mood);
    formData.append("voice_file", file, "checkin.wav");

    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/parent/checkins`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Failed to upload check-in");
    }
    return res.json();
  },

  getSlots: (week?: string) =>
    apiFetch(week ? `/parent/slots?week=${week}` : "/parent/slots"),

  bookCall: (payload: {
    day: string;
    date?: string;
    window_id?: string;
    time: string;
    method?: string;
    reminders?: string[];
  }) =>
    apiFetch("/parent/bookings", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  cancelBooking: (id: string) =>
    apiFetch(`/parent/bookings/${id}`, { method: "DELETE" }),

  getIcsUrl: (id: string) =>
    `${API_BASE}/parent/bookings/${id}.ics`,

  downloadIcs: async (id: string) => {
    const token = localStorage.getItem("edupulse_token");
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/parent/bookings/${id}.ics`, { headers });
    if (!res.ok) throw new Error("Could not download .ics");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `edupulse-call-${id}.ics`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  },

  updatePreferences: (payload: {
    channel?: string;
    language?: string;
    no_smartphone?: boolean;
    shift_worker?: boolean;
  }) =>
    apiFetch("/parent/preferences", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
};

// =========================================================================
// VOICE SIMULATOR API METHODS
// =========================================================================

export const voiceApi = {
  simulate: (keypad_input: string) =>
    apiFetch("/voice/simulate", {
      method: "POST",
      body: JSON.stringify({ keypad_input }),
    }),
};

// =========================================================================
// CLASS GARDEN API METHODS
// =========================================================================

export const gardenApi = {
  getClassGarden: (className?: string) =>
    apiFetch(className ? `/garden/${className}` : "/garden"),
};

// =========================================================================
// ADMIN API METHODS
// =========================================================================

export const adminApi = {
  getOverview: () =>
    apiFetch("/admin/overview"),

  getGuardrails: () =>
    apiFetch("/admin/guardrails"),

  updateSettings: (feature_flags: Record<string, any>) =>
    apiFetch("/admin/settings", {
      method: "PATCH",
      body: JSON.stringify({ feature_flags }),
    }),

  getAuditLogs: (params?: {
    actor_id?: string;
    actor_role?: string;
    action?: string;
    limit?: number;
    offset?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.actor_id) q.set("actor_id", params.actor_id);
    if (params?.actor_role) q.set("actor_role", params.actor_role);
    if (params?.action) q.set("action", params.action);
    if (params?.limit) q.set("limit", params.limit.toString());
    if (params?.offset) q.set("offset", params.offset.toString());
    return apiFetch(`/admin/audit-logs?${q.toString()}`);
  },
};
