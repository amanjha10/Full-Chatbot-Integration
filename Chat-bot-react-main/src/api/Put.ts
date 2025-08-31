import { axiosClient } from "../config/axiosConfig";
import type { CompanyPayloadType } from "../type/super-admin/SuperAdminTypeData";

export const editCompany=(data:CompanyPayloadType,id:number)=>axiosClient.put(`/auth/update-admin/${id}/`,data)