import type {
  Assignment,
  DashboardData,
  Maddie,
  Task,
  User,
} from "./types";

const ACCESS_KEY = "maddies_access";
const REFRESH_KEY = "maddies_refresh";

export class ApiError extends Error {
  status: number;
  data: unknown;
  constructor(status: number, data: unknown) {
    super(`API error ${status}`);
    this.status = status;
    this.data = data;
  }
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) return false;
  const res = await fetch("/api/auth/token/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    clearTokens();
    return false;
  }
  const data = await res.json();
  localStorage.setItem(ACCESS_KEY, data.access);
  return true;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retry = true
): Promise<T> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  const token = getAccessToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(path, { ...options, headers });

  if (res.status === 401 && retry && (await refreshAccessToken())) {
    return request<T>(path, options, false);
  }
  if (!res.ok) {
    let data: unknown = null;
    try {
      data = await res.json();
    } catch {
      /* non-JSON */
    }
    throw new ApiError(res.status, data);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// Auth
export async function login(email: string, password: string) {
  const res = await fetch("/api/auth/token/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new ApiError(res.status, await res.json().catch(() => null));
  const data = await res.json();
  setTokens(data.access, data.refresh);
}

export const me = () => request<User>("/api/auth/me/");
export const dashboard = () => request<DashboardData>("/api/dashboard/");

// Users
export const listUsers = () => request<User[]>("/api/users/");
export const createUser = (payload: Partial<User> & { password: string }) =>
  request<User>("/api/users/", { method: "POST", body: JSON.stringify(payload) });

// Maddies
export const listMaddies = () => request<Maddie[]>("/api/maddies/");
export const getMaddie = (id: string) => request<Maddie>(`/api/maddies/${id}/`);
export const createMaddie = (payload: Partial<Maddie>) =>
  request<Maddie>("/api/maddies/", { method: "POST", body: JSON.stringify(payload) });
export const updateMaddie = (id: string, payload: Partial<Maddie>) =>
  request<Maddie>(`/api/maddies/${id}/`, { method: "PATCH", body: JSON.stringify(payload) });

// Assignments
export const listAssignments = () => request<Assignment[]>("/api/assignments/");
export const createAssignment = (payload: Partial<Assignment>) =>
  request<Assignment>("/api/assignments/", { method: "POST", body: JSON.stringify(payload) });
export const completeAssignment = (id: string) =>
  request<Assignment>(`/api/assignments/${id}/complete/`, { method: "POST" });

// Tasks
export const listTasks = () => request<Task[]>("/api/tasks/");
export const createTask = (payload: Partial<Task>) =>
  request<Task>("/api/tasks/", { method: "POST", body: JSON.stringify(payload) });
export const advanceTask = (id: string) =>
  request<Task>(`/api/tasks/${id}/advance/`, { method: "POST" });
