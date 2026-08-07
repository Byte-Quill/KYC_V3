import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, useAuth } from "./auth";
import Layout from "./components/Layout";

// Route-level code splitting: pages load on demand instead of one big bundle.
const ApplicationDetailPage = lazy(() => import("./pages/ApplicationDetailPage"));
const ApplicationFormPage = lazy(() => import("./pages/ApplicationFormPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const RegisterPage = lazy(() => import("./pages/RegisterPage"));
const ReviewDetailPage = lazy(() => import("./pages/ReviewDetailPage"));
const ReviewQueuePage = lazy(() => import("./pages/ReviewQueuePage"));

function PageLoader() {
  return <p className="p-8 text-center text-slate-500">Loading…</p>;
}

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
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
      <Suspense fallback={<PageLoader />}>
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
      </Suspense>
    </AuthProvider>
  );
}
