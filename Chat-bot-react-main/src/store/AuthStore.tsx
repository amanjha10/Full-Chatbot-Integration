import React, { createContext, useContext, useState, useEffect } from "react";
type AuthType = {
  role: string | null;
  adminId: string | null;
  isAuth: string | null;
  setRole: (arg: string | null) => void;
  setIsAuth: (arg: string | null) => void;
  setAdminId: (arg: string | null) => void;
};
const AuthContext = createContext<AuthType | undefined>(undefined);
export default function AuthContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  // Initialize state directly from localStorage
  const [isAuth, setIsAuth] = useState<string | null>(() => {
    return localStorage.getItem("isAuth");
  });
  const [role, setRole] = useState<string | null>(() => {
    return localStorage.getItem("role");
  });
  const [adminId, setAdminId] = useState<string | null>(() => {
    return localStorage.getItem("adminId");
  });

  console.log("DEBUG: AuthStore state:", {
    isAuth,
    role,
    adminId,
  });
  // Custom setters that update both state and localStorage
  const updateIsAuth = (value: string | null) => {
    setIsAuth(value);
    if (value) {
      localStorage.setItem("isAuth", value);
    } else {
      localStorage.removeItem("isAuth");
    }
  };

  const updateRole = (value: string | null) => {
    setRole(value);
    if (value) {
      localStorage.setItem("role", value);
    } else {
      localStorage.removeItem("role");
    }
  };

  const updateAdminId = (value: string | null) => {
    setAdminId(value);
    if (value) {
      localStorage.setItem("adminId", value);
    } else {
      localStorage.removeItem("adminId");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        role,
        isAuth,
        setIsAuth: updateIsAuth,
        setRole: updateRole,
        adminId,
        setAdminId: updateAdminId,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) return;
  return context;
};
