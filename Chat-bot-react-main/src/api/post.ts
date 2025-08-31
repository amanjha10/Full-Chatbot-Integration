import { axiosClient } from "../config/axiosConfig";
import type { CreateAgentPayload, ResetPasswordPayload } from "../type/admin/AdminDataType";
import type { CompanyPayloadType, PlanPayloadType } from "../type/super-admin/SuperAdminTypeData";

export const Login=(data:{username:string,password:string})=>axiosClient.post('/auth/login/',data);
export const createCompany=(data:CompanyPayloadType)=>axiosClient.post('/auth/create-admin/',data);
export const createPlan=(data:PlanPayloadType)=>axiosClient.post('/auth/create-plan/',data);
export const createAgent=(data:CreateAgentPayload)=>axiosClient.post('/admin-dashboard/create-agent/',data);
export const resetPassword=(data:ResetPasswordPayload)=>axiosClient.post('/admin-dashboard/reset-agent-password/',data);