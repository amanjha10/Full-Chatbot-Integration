import { lazy } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import AppLayout from "../layout/AppLayout";
import PageNotFound from "../components/PageNotFound";
// import RoleBaseRouting from "./RoleBaseRouting";
const Dashboard = lazy(() => import("../page/Dashboard"));
const UserManagement = lazy(() => import("../page/UserManagement"));
const ManageAgent = lazy(() => import("../page/ManageAgent"));
const Chat = lazy(() => import("../page/Chat"));
const Login = lazy(() => import("../page/Login"));
const SuperAdminDashboard = lazy(() => import("../page/super-admin/Dashboard"));
const SuperAdminPlan = lazy(() => import("../page/super-admin/Plan"));
const SuperAdminCompany = lazy(() => import("../page/super-admin/Company"));
const SuperAdminFAQ = lazy(() => import("../page/super-admin/FAQ"));
const CompanyFAQ = lazy(() => import("../page/CompanyFAQ"));
const AgentDashboard = lazy(() => import("../page/agent/Dashboard"));
const ProtectedRouting = lazy(() => import("../router/ProtectedRouting"));
const Settings = lazy(() => import("../page/Settings"));
const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/app/dashboard" replace />,
  },
  {
    path: "/login",
    element: <Login />,
  },
  {
    path: "*",
    element: <PageNotFound />,
  },
  {
    path: "/app",
    element: (
      <ProtectedRouting roles={["ADMIN"]}>
        <AppLayout />
      </ProtectedRouting>
    ),
    children: [
      {
        path: "dashboard",
        element: <Dashboard />,
      },
      {
        path: "user-management",
        element: <UserManagement />,
      },
      {
        path: "agent-management",
        element: <ManageAgent />,
      },
      {
        path: "settings",
        element: <Settings />,
      },
      {
        path: "chat",
        element: <Chat />,
      },
      {
        path: "company-faq",
        element: <CompanyFAQ />,
      },
    ],
  },
  {
    path: "/super-admin",
    element: (
      <ProtectedRouting roles={["SUPERADMIN"]}>
        <AppLayout />
      </ProtectedRouting>
    ),
    children: [
      {
        path: "dashboard",
        element: <SuperAdminDashboard />,
      },
      {
        path: "plan",
        element: <SuperAdminPlan />,
      },
      {
        path: "company",
        element: <SuperAdminCompany />,
      },
      {
        path: "faq",
        element: <SuperAdminFAQ />,
      },
    ],
  },
  {
    path: "/agent",
    element: (
      <ProtectedRouting roles={["AGENT"]}>
        <AppLayout />
      </ProtectedRouting>
    ),
    children: [
      {
        path: "dashboard",
        element: <AgentDashboard />,
      },
    ],
  },
]);

export default router;
