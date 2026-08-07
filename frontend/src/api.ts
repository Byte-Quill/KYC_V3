import type { ApplicationPayload, AuditEntry, KYCApplication, Page, User } from "./types";

const BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL.replace(/\/$/, "")}/api`
  : "/api";

let accessToken: string | null = localStorage.getItem("access");
let refreshToken: string | null = localStorage.getItem("refresh");

export function setTokens(access: string, refresh: string) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem("access", access);
  localStorage.setItem("refresh", refresh);
}

export function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
}

export function isAuthenticated() {
  return !!accessToken;
}

async function refreshAccess(): Promise<boolean> {
  if (!refreshToken) return false;
  const res = await fetch(`${BASE}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  if (!res.ok) {
    clearTokens();
    return false;
  }
  const data = await res.json();
  accessToken = data.access;
  localStorage.setItem("access", data.access);
  if (data.refresh) {
    refreshToken = data.refresh;
    localStorage.setItem("refresh", data.refresh);
  }
  return true;
}

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown) {
    super(`API error ${status}`);
    this.status = status;
    this.body = body;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers });

  if (res.status === 401 && retry && (await refreshAccess())) {
    return request<T>(path, options, false);
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const login = (email: string, password: string) =>
  request<{ access: string; refresh: string }>("/auth/token/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const register = (payload: {
  email: string;
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
}) =>
  request<User>("/auth/register/", { method: "POST", body: JSON.stringify(payload) });

export const fetchMe = () => request<User>("/auth/me/");

export const listApplications = (page = 1) =>
  request<Page<KYCApplication>>(`/applications/?page=${page}`);
export const getApplication = (id: string) => request<KYCApplication>(`/applications/${id}/`);
export const createApplication = (payload: ApplicationPayload) =>
  request<KYCApplication>("/applications/", { method: "POST", body: JSON.stringify(payload) });
export const updateApplication = (id: string, payload: Partial<ApplicationPayload>) =>
  request<KYCApplication>(`/applications/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
export const submitApplication = (id: string) =>
  request<KYCApplication>(`/applications/${id}/submit/`, { method: "POST" });

export const uploadDocument = (id: string, docType: string, file: File) => {
  const form = new FormData();
  form.append("doc_type", docType);
  form.append("file", file);
  return request<{ id: string }>(`/applications/${id}/documents/`, {
    method: "POST",
    body: form,
  });
};

export const reviewApplication = (id: string, decision: string, notes: string) =>
  request<KYCApplication>(`/applications/${id}/review/`, {
    method: "POST",
    body: JSON.stringify({ decision, notes }),
  });

export const fetchAudit = (id: string) => request<AuditEntry[]>(`/applications/${id}/audit/`);
export const fetchReviewQueue = (page = 1) =>
  request<Page<KYCApplication>>(`/review-queue/?page=${page}`);
