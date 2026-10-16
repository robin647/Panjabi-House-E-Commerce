// Thin client for the Django REST API.
//
// Every successful response is {success, message, data, meta?}; every error is
// {success:false, message, errors, code}. This module unwraps both, silently
// refreshes an expired access token once, and exposes one ApiError shape.

const BASE = (import.meta.env.VITE_API_BASE || "/api/v1").replace(/\/$/, "");
const TOKEN_KEY = "shop.tokens";

export class ApiError extends Error {
  constructor(message, { status = 0, errors = {}, code = "error" } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.errors = errors;
    this.code = code;
  }
}

export const tokenStore = {
  get() {
    try {
      return JSON.parse(localStorage.getItem(TOKEN_KEY));
    } catch {
      return null;
    }
  },
  set(tokens) {
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
  },
};

let onAuthLost = () => {};
export function setAuthLostHandler(fn) {
  onAuthLost = fn;
}

let refreshing = null;
function refreshTokens() {
  const tokens = tokenStore.get();
  if (!tokens?.refresh) return Promise.reject(new Error("No refresh token"));
  if (!refreshing) {
    refreshing = fetch(`${BASE}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: tokens.refresh }),
    })
      .then(async (res) => {
        const body = await res.json().catch(() => null);
        if (!res.ok || !body?.success) throw new Error("Refresh failed");
        tokenStore.set(body.data);
        return body.data;
      })
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
}

function buildUrl(path, query) {
  if (!query) return `${BASE}${path}`;
  const params = new URLSearchParams();
  Object.entries(query).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "" && v !== false) params.set(k, String(v));
  });
  const qs = params.toString();
  return `${BASE}${path}${qs ? `?${qs}` : ""}`;
}

export async function request(path, { method = "GET", body, auth = false, headers = {}, query, _retried = false } = {}) {
  const finalHeaders = { Accept: "application/json", ...headers };
  if (body !== undefined) finalHeaders["Content-Type"] = "application/json";
  if (auth) {
    const tokens = tokenStore.get();
    if (tokens?.access) finalHeaders.Authorization = `Bearer ${tokens.access}`;
  }

  let res;
  try {
    res = await fetch(buildUrl(path, query), {
      method,
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Can't reach the server. Check your connection and try again.", { code: "network_error" });
  }

  if (res.status === 401 && auth && !_retried) {
    try {
      await refreshTokens();
      return request(path, { method, body, auth, headers, query, _retried: true });
    } catch {
      tokenStore.clear();
      onAuthLost();
      throw new ApiError("Your session has expired. Please sign in again.", { status: 401, code: "session_expired" });
    }
  }

  const payload = await res.json().catch(() => null);
  if (res.ok && payload?.success !== false) {
    return { data: payload?.data ?? null, meta: payload?.meta ?? null, message: payload?.message ?? "" };
  }
  throw new ApiError(payload?.message || "Something went wrong. Please try again.", {
    status: res.status,
    errors: payload?.errors || {},
    code: payload?.code || "error",
  });
}

export const api = {
  get: (path, opts) => request(path, { ...opts, method: "GET" }),
  post: (path, body, opts) => request(path, { ...opts, method: "POST", body }),
  patch: (path, body, opts) => request(path, { ...opts, method: "PATCH", body }),
  delete: (path, opts) => request(path, { ...opts, method: "DELETE" }),
};
