import type { ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, useAuth } from "./auth";
import Layout from "./components/Layout";
import ApplicationDetailPage from "./pages/ApplicationDetailPage";
import ApplicationFormPage from "./pages/ApplicationFormPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ReviewDetailPage from "./pages/ReviewDetailPage";
import ReviewQueuePage from "./pages/ReviewQueuePage";

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="p-8 text-center text-slate-500">Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function ReviewerOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (!user || (user.role !== "reviewer" && user.role !== "admin")) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          element={
            <Protected>
              <Layout />
            </Protected>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/applications/new" element={<ApplicationFormPage />} />
          <Route path="/applications/:id" element={<ApplicationDetailPage />} />
          <Route
            path="/review"
            element={
              <ReviewerOnly>
                <ReviewQueuePage />
              </ReviewerOnly>
            }
          />
          <Route
            path="/review/:id"
            element={
              <ReviewerOnly>
                <ReviewDetailPage />
              </ReviewerOnly>
            }
          />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
