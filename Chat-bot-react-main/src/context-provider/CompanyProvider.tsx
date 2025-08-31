import React, { createContext, useContext, useState, useEffect } from "react";
import { axiosClient } from "../config/axiosConfig";

interface CompanyInfo {
  id: number;
  company_id: string;
  name: string;
  email: string;
  contact_person: string;
  contact_number: string;
  phone_number: string;
  address: string;
  plan_name: string;
  plan_id: number;
  date_joined: string;
  is_active: boolean;
}

interface CompanyContextType {
  companyInfo: CompanyInfo | null;
  companyId: string | null;
  isLoading: boolean;
  error: string | null;
  refreshCompanyInfo: () => Promise<void>;
  setCompanyId: (id: string) => void;
}

const CompanyContext = createContext<CompanyContextType | undefined>(undefined);

interface CompanyProviderProps {
  children: React.ReactNode;
}

export default function CompanyProvider({ children }: CompanyProviderProps) {
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [companyId, setCompanyIdState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Get company_id from localStorage or user profile
  useEffect(() => {
    const initializeCompanyId = async () => {
      // First try to get from localStorage (for admin/agent users)
      const storedCompanyId = localStorage.getItem("company_id");
      if (storedCompanyId) {
        setCompanyIdState(storedCompanyId);
        return;
      }

      // If not found, try to get from user profile
      try {
        const token = localStorage.getItem("access_token");
        if (token) {
          const response = await axiosClient.get("/auth/profile/");
          if (response.data.company_id) {
            setCompanyIdState(response.data.company_id);
            localStorage.setItem("company_id", response.data.company_id);
          }
        }
      } catch (error) {
        console.error("Failed to get company_id from profile:", error);
      }
    };

    initializeCompanyId();
  }, []);

  // Fetch company information when companyId changes
  useEffect(() => {
    if (companyId) {
      fetchCompanyInfo();
    }
  }, [companyId]);

  const fetchCompanyInfo = async () => {
    if (!companyId) return;

    setIsLoading(true);
    setError(null);

    try {
      // For SuperAdmin, we can get company info by company_id
      // For Admin/Agent, we get their own company info
      const userRole = localStorage.getItem("role");

      if (userRole === "SUPERADMIN") {
        // SuperAdmin can query any company
        const response = await axiosClient.get(
          `/auth/list-admins/?search=${companyId}`
        );
        const companies = response.data.results || response.data;
        const company = Array.isArray(companies)
          ? companies.find((c: CompanyInfo) => c.company_id === companyId)
          : companies;

        if (company) {
          setCompanyInfo(company);
        } else {
          setError("Company not found");
        }
      } else {
        // Admin/Agent gets their own company info
        const response = await axiosClient.get("/auth/profile/");
        if (response.data.company_id === companyId) {
          // For regular admins, use their profile data directly
          if (response.data.role === "ADMIN") {
            setCompanyInfo({
              id: response.data.id,
              name: response.data.name,
              email: response.data.username,
              company_id: response.data.company_id,
              role: response.data.role,
            });
          } else if (response.data.role === "SUPERADMIN") {
            // For SuperAdmin, get detailed admin list (restricted to SuperAdmin only)
            try {
              const adminResponse = await axiosClient.get(
                `/auth/list-admins/?admin_id=${response.data.id}`
              );
              setCompanyInfo(adminResponse.data);
            } catch (error) {
              // Fallback to profile data if list-admins fails
              setCompanyInfo({
                id: response.data.id,
                name: response.data.name,
                email: response.data.username,
                company_id: response.data.company_id,
                role: response.data.role,
              });
            }
          } else {
            // For other roles (AGENT), use profile data
            setCompanyInfo({
              id: response.data.id,
              name: response.data.name,
              email: response.data.username,
              company_id: response.data.company_id,
              role: response.data.role,
            });
          }
        } else {
          setError("Access denied to this company");
        }
      }
    } catch (error: any) {
      setError(
        error?.response?.data?.error || "Failed to fetch company information"
      );
      console.error("Error fetching company info:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshCompanyInfo = async () => {
    await fetchCompanyInfo();
  };

  const setCompanyId = (id: string) => {
    setCompanyIdState(id);
    localStorage.setItem("company_id", id);
  };

  const contextValue: CompanyContextType = {
    companyInfo,
    companyId,
    isLoading,
    error,
    refreshCompanyInfo,
    setCompanyId,
  };

  return (
    <CompanyContext.Provider value={contextValue}>
      {children}
    </CompanyContext.Provider>
  );
}

// Custom hook to use the company context
export function useCompany() {
  const context = useContext(CompanyContext);
  if (context === undefined) {
    throw new Error("useCompany must be used within a CompanyProvider");
  }
  return context;
}

// Hook to get company_id for API calls
export function useCompanyId() {
  const { companyId } = useCompany();
  return companyId;
}

// Hook to ensure company isolation in API calls
export function useCompanyFilter() {
  const { companyId } = useCompany();

  const getCompanyFilter = () => {
    const userRole = localStorage.getItem("role");

    // SuperAdmin can access all companies, others are restricted to their company
    if (userRole === "SUPERADMIN") {
      return {}; // No filter for SuperAdmin
    }

    return companyId ? { company_id: companyId } : {};
  };

  const addCompanyFilter = (params: Record<string, any> = {}) => {
    const filter = getCompanyFilter();
    return { ...params, ...filter };
  };

  return {
    companyId,
    getCompanyFilter,
    addCompanyFilter,
  };
}

// Utility function to validate company access
export function validateCompanyAccess(targetCompanyId: string): boolean {
  const userRole = localStorage.getItem("role");
  const userCompanyId = localStorage.getItem("company_id");

  // SuperAdmin can access any company
  if (userRole === "SUPERADMIN") {
    return true;
  }

  // Admin/Agent can only access their own company
  return userCompanyId === targetCompanyId;
}

// Utility function to get company-specific WebSocket URL
export function getCompanyWebSocketUrl(
  endpoint: string,
  companyId?: string
): string {
  const wsCompanyId =
    companyId || localStorage.getItem("company_id") || "DEFAULT_COMPANY";
  const baseUrl =
    process.env.NODE_ENV === "production"
      ? "wss://your-domain.com"
      : "ws://localhost:8000";

  return `${baseUrl}/ws/${endpoint}/${wsCompanyId}/`;
}

// Utility function to ensure all API calls include company context
export function withCompanyContext(apiCall: () => Promise<any>) {
  return async () => {
    const companyId = localStorage.getItem("company_id");
    if (!companyId && localStorage.getItem("role") !== "SUPERADMIN") {
      throw new Error("Company context not available");
    }
    return apiCall();
  };
}
