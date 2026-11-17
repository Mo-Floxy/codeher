// Same-origin by default: the Vite dev/preview servers and vercel.json each proxy /api to
// whichever Django instance is meant to answer. A hard-coded localhost would be baked
// into the deployed bundle and send every visitor's requests to their own machine.
const RAW_BASE = import.meta.env.VITE_API_BASE_URL || "/api";
export const API_BASE = RAW_BASE.replace(/\/+$/, "");

const ACCESS_KEY = "codeher.access";
const REFRESH_KEY = "codeher.refresh";

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiError extends Error {
  constructor(status, payload) {
    super(status === 401 ? "Please sign in again." : "Something went wrong.");
    this.name = "ApiError";
    this.status = status;
    this.payload = payload ?? null;
    this.fieldErrors = normalizeFieldErrors(payload);
    this.detail = payload?.detail ?? "";
  }

  /** First message for a field, or the flattened detail — for inline form errors. */
  messageFor(field) {
    const list = this.fieldErrors[field];
    if (list?.length) return list[0];
    if (this.detail) return this.detail;
    return this.message;
  }
}

function normalizeFieldErrors(payload) {
  const out = {};
  if (!payload || typeof payload !== "object") return out;
  for (const [key, value] of Object.entries(payload)) {
    if (key === "detail" || key === "code" || key === "status") continue;
    if (Array.isArray(value)) out[key] = value.map(String);
    else if (typeof value === "object") out[key] = [String(value)];
    else if (value != null) out[key] = [String(value)];
  }
  if (payload.detail) out.__default__ = [String(payload.detail)];
  return out;
}

/** Listeners get notified when the session is lost so the auth context can reset. */
const unauthorizedListeners = new Set();
export function onUnauthorized(fn) {
  unauthorizedListeners.add(fn);
  return () => unauthorizedListeners.delete(fn);
}

let refreshInFlight = null;

/**
 * Clear the session and tell listeners exactly once, even though the 401
 * branch and the failing-response branch below can both reach it in one call.
 */
function loseSession() {
  if (!tokenStore.access && !tokenStore.refresh) return;
  tokenStore.clear();
  unauthorizedListeners.forEach((fn) => fn());
}

async function refreshAccessToken() {
  const refresh = tokenStore.refresh;
  if (!refresh) return null;
  if (!refreshInFlight) {
    refreshInFlight = fetch(`${API_BASE}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    })
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (data?.access) tokenStore.set({ access: data.access });
        return data?.access ?? null;
      })
      .catch(() => null)
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

function buildQuery(params) {
  if (!params) return "";
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      if (value.length) search.set(key, value.join(","));
    } else {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `?${query}` : "";
}

/** Unauthenticated endpoints whose 401 means "wrong credentials". */
const AUTH_ENTRY_PATHS = ["/auth/login/", "/auth/register/", "/auth/password/forgot/", "/auth/password/reset/"];

async function request(path, { method = "GET", body, params, formData, headers, retry = true, signal } = {}) {
  const isForm = formData instanceof FormData;
  const token = tokenStore.access;
  // These endpoints answer 401 to mean "wrong credentials", not "your session expired",
  // so a rejected attempt there must never refresh or clear the session in store.
  const authEntry = AUTH_ENTRY_PATHS.includes(path);

  const init = {
    method,
    signal,
    headers: {
      Accept: "application/json",
      ...(isForm ? {} : body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  };
  if (isForm) init.body = formData;
  else if (body !== undefined) init.body = JSON.stringify(body);

  let response;
  try {
    response = await fetch(`${API_BASE}${path}${buildQuery(params)}`, init);
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new ApiError(0, { detail: "Cannot reach the CodeHer API. Is the backend running?" });
  }

  if (response.status === 401 && !authEntry && retry && tokenStore.refresh) {
    const fresh = await refreshAccessToken();
    if (fresh) {
      return request(path, { method, body, params, formData, headers, retry: false, signal });
    }
    loseSession();
  }

  if (response.status === 204 || response.headers.get("content-length") === "0") {
    return null;
  }

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json().catch(() => null)
    : await response.text().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 && !authEntry) loseSession();
    throw new ApiError(response.status, payload);
  }
  return payload;
}

export const api = {
  get: (path, options) => request(path, options),
  post: (path, body, options) => request(path, { ...options, method: "POST", body }),
  patch: (path, body, options) => request(path, { ...options, method: "PATCH", body }),
  put: (path, body, options) => request(path, { ...options, method: "PUT", body }),
  del: (path, options) => request(path, { ...options, method: "DELETE" }),
  upload: (path, formData, options) => request(path, { ...options, method: "POST", formData }),
  request,
};

export const endpoints = {
  register: "/auth/register/",
  login: "/auth/login/",
  logout: "/auth/logout/",
  me: "/auth/me/",
  forgotPassword: "/auth/password/forgot/",
  resetPassword: "/auth/password/reset/",
  myProfile: "/users/me/profile/",
  dashboard: "/dashboard/",
  paths: "/learning/paths/",
  courses: "/learning/courses/",
  enrollments: "/learning/me/enrollments/",
  certificates: "/learning/me/certificates/",
  challenges: "/challenges/",
  challengeLeaderboard: "/challenges/leaderboard/",
  mySubmissions: "/challenges/submissions/me/",
  posts: "/community/posts/",
  projects: "/community/projects/",
  mentors: "/mentorship/mentors/",
  mentorRequests: "/mentorship/requests/",
  notifications: "/notifications/",
  unreadCount: "/notifications/unread-count/",
  achievements: "/achievements/",
  myAchievements: "/achievements/me/",
  goals: "/achievements/me/goals/",
  adminOverview: "/admin/overview/",
  adminAnalytics: "/admin/analytics/",
  adminUsers: "/admin/users/",
  adminReports: "/admin/reports/",
};
