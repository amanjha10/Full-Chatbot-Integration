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
