import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { schemaOfLogin } from "../schema";
import type z from "zod";
import { Login } from "../api/post";
import { useNavigate } from "react-router-dom";
import { useMessageContext } from "../context-provider/MessageProvider";
import { useAuth } from "../store/AuthStore";
import { axiosClient } from "../config/axiosConfig";
type FormType = z.infer<typeof schemaOfLogin>;
interface LoginProps {
  setLoading: (arg: boolean) => void;
  setIsFirstLogin?: (arg: boolean) => void;
  setFirstLoginData?: (arg: { email: string; password: string } | null) => void;
}
export const useLogin = ({
  setLoading,
  setIsFirstLogin,
  setFirstLoginData,
}: LoginProps) => {
  const context = useAuth();
  const navigate = useNavigate();
  const { messageApi } = useMessageContext();
  const formHooks = useForm({
    mode: "onChange",
    resolver: zodResolver(schemaOfLogin),
    defaultValues: {
      email: "",
      password: "",
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  });
  const { handleSubmit, getValues } = formHooks;

  const onSubmit = (data: FormType) => {
    console.log("DEBUG: Form submitted with data:", data);
    setLoading(true);

    // Check if this is a first login submission
    if (data.current_password && data.new_password && data.confirm_password) {
      console.log("DEBUG: Handling first login submission");
      handleFirstLoginSubmit(data);
    } else {
      console.log("DEBUG: Handling normal login submission");
      handleNormalLogin(data);
    }
  };

  const handleNormalLogin = (data: FormType) => {
    console.log("DEBUG: Starting normal login with data:", data);
    const formDTO = {
      username: data?.email,
      password: data?.password,
    };
    console.log("DEBUG: Sending login request with:", formDTO);

    Login(formDTO)
      .then((res) => {
        console.log("DEBUG: Login response:", res);

        // Handle first login case (both agent and admin)
        if (res?.data?.is_first_login) {
          const userRole = res?.data?.user?.role || "AGENT";
          console.log("DEBUG: First login detected - userRole:", userRole);
          console.log("DEBUG: Full response data for first login:", res?.data);

          const message = userRole === "ADMIN"
            ? "Please set your new password to continue as Admin."
            : "Please set your new password to continue.";

          // Store role temporarily for first login endpoint selection
          localStorage.setItem("temp_first_login_role", userRole);
          console.log("DEBUG: Stored role in localStorage:", userRole);

          messageApi.info(message);
          setIsFirstLogin?.(true);
          setFirstLoginData?.({
            email: res?.data?.email,
            password: data?.password,
          });
          setLoading(false);
          return;
        }

        // Handle normal login navigation
        console.log("DEBUG: User role from response:", res?.data?.user?.role);
        console.log("DEBUG: Full response data:", res?.data);

        if (res?.data?.user?.role == "SUPERADMIN") {
          console.log("DEBUG: Navigating to super-admin dashboard");
          navigate("/super-admin/dashboard");
        } else if (res?.data?.user?.role == "ADMIN") {
          console.log("DEBUG: Navigating to admin dashboard");
          navigate("/app/dashboard");
        } else if (res?.data?.user?.role == "AGENT") {
          console.log("DEBUG: Navigating to agent dashboard");
          navigate("/agent/dashboard");
        } else {
          console.log("DEBUG: Default navigation to agent dashboard");
          navigate("/agent/dashboard");
        }

        // Store authentication data
        const userRole = res?.data?.user?.role || "AGENT";
        const userId = res?.data?.user?.id || res?.data?.agent?.id;
        const companyId =
          res?.data?.user?.company_id ||
          res?.data?.agent?.company_id ||
          "DEFAULT_COMPANY";

        // DEAD CODE REMOVED - Debug console.log statements removed for production

        localStorage.setItem("access_token", res?.data?.access);
        localStorage.setItem("adminId", userId);
        localStorage.setItem("company_id", companyId);
        localStorage.setItem("role", userRole);
        localStorage.setItem("isAuth", "true");

        context?.setIsAuth("true");
        context?.setRole(userRole);
        setLoading(false);
        messageApi.success("Login Successfully");
      })
      .catch((err) => {
        console.log("DEBUG: Login error:", err);
        console.log("DEBUG: Error response:", err?.response);
        console.log("DEBUG: Error data:", err?.response?.data);
        setLoading(false);

        // Handle different error types
        if (err?.response?.data?.error) {
          messageApi.error(err.response.data.error);
        } else if (err?.response?.data?.non_field_errors?.[0]) {
          messageApi.error(err.response.data.non_field_errors[0]);
        } else if (err?.response?.data?.detail) {
          messageApi.error(err.response.data.detail);
        } else if (err?.message) {
          messageApi.error(err.message);
        } else {
          messageApi.error("Login failed. Please try again.");
        }
      });
  };

  const handleFirstLoginSubmit = async (data: FormType) => {
    console.log("DEBUG: Starting first login submit with data:", data);
    try {
      // Validate passwords match
      if (data.new_password !== data.confirm_password) {
        console.log("DEBUG: Passwords don't match");
        messageApi.error("New passwords do not match");
        setLoading(false);
        return;
      }

      const firstLoginData = getValues();
      console.log("DEBUG: First login data from form:", firstLoginData);

      // Determine if this is admin or agent first login based on stored data
      // We need to check the user role from the previous login attempt
      const storedRole = localStorage.getItem("temp_first_login_role");
      const isAdminFirstLogin = storedRole === "ADMIN";

      console.log("DEBUG: Retrieved stored role:", storedRole);
      console.log("DEBUG: Is admin first login:", isAdminFirstLogin);

      const endpoint = isAdminFirstLogin
        ? "/auth/admin-first-login/"
        : "/admin-dashboard/agent-first-login/";

      console.log("DEBUG: Using endpoint:", endpoint, "for role:", storedRole);

      await axiosClient.post(endpoint, {
        email: firstLoginData.email,
        current_password: data.current_password,
        new_password: data.new_password,
        confirm_password: data.confirm_password,
      });

      messageApi.success(
        "Password updated successfully! Please login with your new password."
      );

      // Clean up temporary role storage
      localStorage.removeItem("temp_first_login_role");

      // Reset form and go back to normal login
      setIsFirstLogin?.(false);
      setFirstLoginData?.(null);
      formHooks.reset({
        email: firstLoginData.email,
        password: "",
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (error: any) {
      messageApi.error(
        error?.response?.data?.error || "Failed to update password"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleFirstLogin = () => {
    // This function can be used to manually trigger first login mode
    setIsFirstLogin?.(true);
  };

  return {
    formHooks,
    formSubmit: handleSubmit(onSubmit),
    handleFirstLogin,
  };
};
