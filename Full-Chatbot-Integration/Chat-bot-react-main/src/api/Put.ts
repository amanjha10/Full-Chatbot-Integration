import { axiosClient } from "../config/axiosConfig";
import type { CompanyPayloadType } from "../type/super-admin/SuperAdminTypeData";

export const editCompany=(data:CompanyPayloadType,id:number)=>axiosClient.put(`/auth/update-admin/${id}/`,data)

// Generic API functions
export const put = <T = any>(url: string, data?: any) => {
  return axiosClient.put<T>(url, data);
};