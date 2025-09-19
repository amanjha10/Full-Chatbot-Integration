import { axiosClient } from "../config/axiosConfig";

export const deleteCompany=(id:number|null)=>axiosClient.delete(`/auth/delete-admin/${id}/`)

// Generic API functions
export const del = <T = any>(url: string) => {
  return axiosClient.delete<T>(url);
};