import { axiosClient } from "../config/axiosConfig";

// Agent limits checking API
export const checkAgentLimits = () =>
  axiosClient.get("/admin-dashboard/check-agent-limit/");

// Plan types API for forms
export const getPlanTypes = () => axiosClient.get("/auth/plan-types/");

// Company subscriptions API
export const getCompanySubscriptions = () =>
  axiosClient.get("/auth/company-subscriptions/");

// List agents API
export const getAgentsList = () =>
  axiosClient.get("/admin-dashboard/list-agents/");

// Plan history API
export const getPlanHistory = (planId: number) =>
  axiosClient.get(`/auth/plan-history/${planId}/`);

// Plan upgrade requests API
export const getPlanUpgradeRequests = () =>
  axiosClient.get("/admin-dashboard/plan-upgrade-requests/");

// Admin dashboard APIs (same as admin dashboard uses)
export const getPendingSessions = () =>
  axiosClient.get("/admin-dashboard/pending-sessions/");

export const getSessionMessages = (sessionId: string, companyId: string) => {
  const params = new URLSearchParams({
    session_id: sessionId,
    company_id: companyId
  });
  return axiosClient.get(`/chatbot/chat-history/?${params.toString()}`);
};

// Generic API functions
export const get = <T = any>(url: string, params?: any) => {
  const fullUrl = params ? `${url}?${new URLSearchParams(params).toString()}` : url;
  return axiosClient.get<T>(fullUrl);
};
