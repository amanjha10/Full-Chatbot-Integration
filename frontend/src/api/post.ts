import { axiosClient } from "../config/axiosConfig";
import type {
  CreateAgentPayload,
  ResetPasswordPayload,
} from "../type/admin/AdminDataType";
import type {
  CompanyPayloadType,
  PlanPayloadType,
} from "../type/super-admin/SuperAdminTypeData";

// Human handoff APIs for admin
export const sendAgentMessage = (data: {
  session_id: string;
  message: string;
  attachment_ids?: number[];
}) => axiosClient.post("/human-handoff/agent/send-message/", data);

export const assignSession = (data: {
  handoff_session_id: number;
  agent_id: number
}) => axiosClient.post("/human-handoff/assign/", data);

export const resolveSession = (data: {
  handoff_session_id: number
}) => axiosClient.post("/human-handoff/resolve/", data);

export const Login = (data: { username: string; password: string }) =>
  axiosClient.post("/auth/login/", data);

// Enhanced company creation with new plan system
export const createCompany = (data: CompanyPayloadType) =>
  axiosClient.post("/auth/create-enhanced-company/", data);

// Legacy company creation (for backward compatibility)
export const createCompanyLegacy = (data: CompanyPayloadType) =>
  axiosClient.post("/auth/create-admin/", data);

export const createPlan = (data: PlanPayloadType) =>
  axiosClient.post("/auth/create-plan/", data);
export const createAgent = (data: CreateAgentPayload) =>
  axiosClient.post("/admin-dashboard/create-agent/", data);
export const resetPassword = (data: ResetPasswordPayload) =>
  axiosClient.post("/admin-dashboard/reset-agent-password/", data);

// Plan History API
export const getPlanHistory = (planId: number) =>
  axiosClient.get(`/auth/plan-history/${planId}/`);

// New Company Subscription APIs
export const getCompanySubscriptions = (params?: string) =>
  axiosClient.get(`/auth/company-subscriptions/${params ? `?${params}` : ""}`);

export const cancelCompanySubscription = (companyId: number, reason?: string) =>
  axiosClient.post(`/auth/cancel-subscription/${companyId}/`, { reason });

export const reactivateCompanySubscription = (companyId: number, planId: number, reason?: string) =>
  axiosClient.post(`/auth/reactivate-subscription/${companyId}/`, { plan_id: planId, reason });

// Subscription management APIs
export const cancelSubscription = (assignmentId: number, reason?: string) =>
  axiosClient.post("/auth/cancel-subscription/", {
    assignment_id: assignmentId,
    reason,
  });

export const renewSubscription = (assignmentId: number, expiryDate?: string) =>
  axiosClient.post("/auth/renew-subscription/", {
    assignment_id: assignmentId,
    expiry_date: expiryDate,
  });

export const upgradePlan = (
  assignmentId: number,
  newPlanId: number,
  reason?: string
) =>
  axiosClient.post("/auth/upgrade-plan/", {
    assignment_id: assignmentId,
    new_plan_id: newPlanId,
    reason,
  });

// Plan upgrade request for admin to superadmin
export const requestPlanUpgrade = (data: {
  requested_plan: string;
  reason?: string;
}) => axiosClient.post("/admin-dashboard/request-plan-upgrade/", data);

// Review plan upgrade request (SuperAdmin only)
export const reviewPlanUpgradeRequest = (
  requestId: number,
  action: "approve" | "decline",
  notes?: string
) =>
  axiosClient.post(
    `/admin-dashboard/plan-upgrade-requests/${requestId}/review/`,
    {
      action,
      notes,
    }
  );

// Generic API functions
export const post = <T = any>(url: string, data?: any) => {
  return axiosClient.post<T>(url, data);
};
