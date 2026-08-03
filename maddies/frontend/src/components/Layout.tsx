import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth";

const ROLE_LABELS: Record<string, string> = {
  ceo: "CEO",
  superadmin: "Super Admin",
  admin: "Admin",
  employee: "Employee",
};

export default function Layout() {
  const { user, logout } = useAuth();
  if (!user) return null;

  const canManage = ["ceo", "superadmin", "admin"].includes(user.role);

  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `block rounded-lg px-4 py-2 text-sm font-medium transition ${
      isActive ? "bg-indigo-600 text-white" : "text-slate-300 hover:bg-slate-800"
    }`;

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 flex-col bg-slate-900 p-4">
        <div className="mb-8 px-2">
          <div className="text-xl font-bold text-white">Maddies</div>
          <div className="text-xs text-slate-400">Workforce Management</div>
        </div>
        <nav className="flex-1 space-y-1">
          <NavLink to="/" end className={linkCls}>Dashboard</NavLink>
          <NavLink to="/maddies" className={linkCls}>Maddies</NavLink>
          <NavLink to="/assignments" className={linkCls}>Assignments</NavLink>
          <NavLink to="/tasks" className={linkCls}>Tasks</NavLink>
          {canManage && <NavLink to="/team" className={linkCls}>Team</NavLink>}
        </nav>
        <div className="border-t border-slate-700 pt-4">
          <div className="px-2 text-sm font-medium text-white">{user.email}</div>
          <div className="px-2 text-xs text-indigo-400">{ROLE_LABELS[user.role]}</div>
          <button
            onClick={logout}
            className="mt-3 w-full rounded-lg bg-slate-800 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700"
          >
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
