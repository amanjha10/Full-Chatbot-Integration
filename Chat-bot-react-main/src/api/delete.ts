import { axiosClient } from "../config/axiosConfig";

export const deleteCompany=(id:number|null)=>axiosClient.delete(`/auth/delete-admin/${id}/`)