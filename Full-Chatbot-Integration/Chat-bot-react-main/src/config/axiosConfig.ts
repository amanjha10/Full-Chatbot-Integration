import axios, { AxiosError, type AxiosResponse } from "axios";
export const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
});

axiosClient.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem("access_token");
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    // Add company context for multi-tenant isolation
    const companyId = localStorage.getItem("company_id");
    const userRole = localStorage.getItem("role");

    // For non-SuperAdmin users, ensure company_id is included in requests
    if (companyId && userRole !== "SUPERADMIN") {
      // Add company_id to query params for GET requests
      if (config.method === "get") {
        config.params = {
          ...config.params,
          company_id: companyId,
        };
      }
      // Add company_id to request body for POST/PUT/PATCH requests
      else if (
        config.method &&
        ["post", "put", "patch"].includes(config.method)
      ) {
        if (config.data instanceof FormData) {
          // For FormData, append company_id
          config.data.append("company_id", companyId);
        } else if (typeof config.data === "object" && config.data !== null) {
          // For JSON data, add company_id to the object
          config.data = {
            ...config.data,
            company_id: companyId,
          };
        }
      }
    }

    return config;
  },
  (error) => Promise.reject(error)
);

axiosClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    // Handle authentication errors
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem("access_token");
      localStorage.removeItem("role");
      localStorage.removeItem("isAuth");
      localStorage.removeItem("adminId");
      localStorage.removeItem("company_id");
      window.location.href = "/login";
    }

    // Handle company access violations
    if (
      error.response?.status === 403 &&
      error.response?.data?.error?.includes("company")
    ) {
      console.error("Company access violation:", error.response.data.error);
      // Could redirect to unauthorized page or show error message
    }

    return Promise.reject(error);
  }
);
