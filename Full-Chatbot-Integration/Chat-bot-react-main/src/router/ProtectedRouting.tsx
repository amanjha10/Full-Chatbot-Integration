import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../store/AuthStore";
interface ProtectdRoutingProps {
  roles: string[];
  children: React.ReactNode;
}
export default function ProtectedRouting({
  children,
  roles,
}: ProtectdRoutingProps) {
  const context = useAuth();
  const token = localStorage.getItem("access_token");
  const isAuthenticated = context?.isAuth === "true" && token;

  console.log("DEBUG: ProtectedRouting check:", {
    isAuth: context?.isAuth,
    hasToken: !!token,
    role: context?.role,
    requiredRoles: roles,
    isAuthenticated,
  });

  if (!isAuthenticated) {
    console.log("DEBUG: Not authenticated, redirecting to login");
    return <Navigate to="/login" replace />;
  }

  if (roles && !roles.includes(context?.role || "")) {
    console.log("DEBUG: Role not authorized, redirecting to login");
    return <Navigate to="/login" replace />;
  }

  console.log("DEBUG: Access granted");
  return <>{children}</>;
}
