export type Role = "ceo" | "superadmin" | "admin" | "employee";

export interface User {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: Role;
  phone: string;
  manager: string | null;
  manager_email: string | null;
}

export type MaddieStatus = "available" | "assigned" | "on_leave" | "inactive";

export interface Maddie {
  id: string;
  full_name: string;
  phone: string;
  email: string;
  address: string;
  skills: string;
  hourly_rate: string;
  status: MaddieStatus;
  photo: string | null;
  managed_by: string | null;
  managed_by_email: string | null;
  active_assignments: number;
  created_at: string;
}

export type AssignmentStatus = "active" | "completed" | "cancelled";

export interface Assignment {
  id: string;
  maddie: string;
  maddie_name: string;
  client_name: string;
  client_address: string;
  start_date: string;
  end_date: string | null;
  status: AssignmentStatus;
  assigned_to: string | null;
  assigned_to_email: string | null;
  notes: string;
  created_at: string;
}

export type TaskStatus = "todo" | "in_progress" | "done";
export type TaskPriority = "low" | "medium" | "high";

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  owner: string;
  owner_email: string;
  assignment: string | null;
  created_at: string;
}

export interface ActivityEntry {
  id: string;
  actor: string | null;
  actor_email: string | null;
  action: string;
  detail: string;
  created_at: string;
}

export interface DashboardData {
  role: Role;
  scope: "organization" | "operations" | "team" | "workspace";
  stats: Record<string, number>;
  maddies_by_status?: { status: MaddieStatus; count: number }[];
  recent_activity?: ActivityEntry[];
  my_maddies?: Maddie[];
  my_tasks?: Task[];
  my_assignments?: Assignment[];
}
