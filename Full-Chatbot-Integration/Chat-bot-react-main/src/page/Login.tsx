import { Avatar, Button, Alert, Divider } from "antd";
import { useLogin } from "../hooks/useLogin";
import AppInput from "../share/form/AppInput";
import AppPassword from "../share/form/AppPassword";
import { FaRegUserCircle } from "react-icons/fa";
import { MdLockReset } from "react-icons/md";
import { useState } from "react";

export default function Login() {
  const [loading, setLoading] = useState(false);
  const [isFirstLogin, setIsFirstLogin] = useState(false);
  const [firstLoginData, setFirstLoginData] = useState<{
    email: string;
    password: string;
  } | null>(null);

  // Get user role for first login context
  const userRole = localStorage.getItem("temp_first_login_role") || "AGENT";
  const isAdminFirstLogin = userRole === "ADMIN";

  const { formHooks, formSubmit, handleFirstLogin } = useLogin({
    setLoading,
    setIsFirstLogin,
    setFirstLoginData,
  });
  const { control } = formHooks;
  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ backgroundColor: "#efefef" }}
    >
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Avatar
            size={100}
            src="https://t3.ftcdn.net/jpg/02/99/04/20/360_F_299042079_vGBD7wIlSeNl7vOevWHiL93G4koMM967.jpg"
            icon={<FaRegUserCircle size={40} />}
          />
          <h1 className="text-3xl font-bold" style={{ color: "#652d90" }}>
            {isFirstLogin
              ? `Set New Password - ${isAdminFirstLogin ? "Admin" : "Agent"}`
              : "System Login"}
          </h1>
          <p className="text-gray-600 mt-2">
            {isFirstLogin
              ? `Complete your ${isAdminFirstLogin ? "admin" : "agent"} account setup`
              : "Consultancy Chatbot System"}
          </p>
        </div>
        <div className="bg-white rounded-2xl shadow-2xl p-8 border border-gray-100">
          <form
            className="space-y-6"
            onSubmit={(e) => {
              e.preventDefault();
              console.log("DEBUG: Form submit event triggered");
              formSubmit(e);
            }}
          >
            {!isFirstLogin ? (
              // Normal Login Fields
              <>
                <AppInput
                  control={control}
                  name="email"
                  label="Email Address"
                  placeholder="Enter email address"
                />
                <AppPassword
                  control={control}
                  name="password"
                  label="Password"
                  placeholder="Enter password"
                />
              </>
            ) : (
              // First Login Fields
              <>
                <Alert
                  message={`${isAdminFirstLogin ? "Admin" : "Agent"} First Login Setup`}
                  description={`Welcome! Please set a new password for ${firstLoginData?.email} (${isAdminFirstLogin ? "Admin Account" : "Agent Account"})`}
                  type="info"
                  icon={<MdLockReset />}
                  className="mb-6"
                />

                <div className="bg-gray-50 p-4 rounded-lg mb-6">
                  <div className="text-sm text-gray-600 mb-2">
                    <strong>Account Details:</strong>
                  </div>
                  <div className="text-sm">
                    <span className="text-gray-500">Email:</span>
                    <span className="ml-2 font-medium">
                      {firstLoginData?.email}
                    </span>
                  </div>
                </div>

                <Divider className="!my-6">Set New Password</Divider>

                <AppPassword
                  control={control}
                  name="current_password"
                  label="Current Password"
                  placeholder="Enter the password provided to you"
                />

                <div className="grid grid-cols-1 gap-4">
                  <AppPassword
                    control={control}
                    name="new_password"
                    label="New Password"
                    placeholder="Enter your new password"
                  />
                  <AppPassword
                    control={control}
                    name="confirm_password"
                    label="Confirm New Password"
                    placeholder="Confirm your new password"
                  />
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-xs text-blue-700">
                    <strong>Password Requirements:</strong>
                    <ul className="mt-2 space-y-1">
                      <li>• At least 6 characters long</li>
                      <li>• Must contain letters and numbers</li>
                      <li>• Both passwords must match</li>
                    </ul>
                  </div>
                </div>
              </>
            )}
            {!isFirstLogin && (
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <input
                    id="remember-me"
                    name="remember-me"
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <label
                    htmlFor="remember-me"
                    className="ml-2 block text-sm text-gray-700"
                  >
                    Remember me
                  </label>
                </div>
                <button
                  type="button"
                  className="text-sm font-medium transition-colors duration-200 hover:opacity-80"
                  style={{ color: "#652d90" }}
                >
                  Forgot password?
                </button>
              </div>
            )}

            <Button
              type="primary"
              htmlType="submit"
              className="w-full !h-12 !text-base !font-semibold"
              loading={loading}
              style={{ backgroundColor: "#652d90", borderColor: "#652d90" }}
            >
              {isFirstLogin ? "Set New Password" : "Sign In"}
            </Button>

            {isFirstLogin && (
              <div className="text-center mt-4">
                <Button
                  type="link"
                  onClick={() => {
                    setIsFirstLogin(false);
                    setFirstLoginData(null);
                  }}
                  className="text-sm"
                  style={{ color: "#652d90" }}
                >
                  Back to Login
                </Button>
              </div>
            )}
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Need access?{" "}
              <button
                type="button"
                className="font-medium transition-colors duration-200 hover:opacity-80"
                style={{ color: "#f7941d" }}
              >
                Contact Administrator
              </button>
            </p>
          </div>
        </div>
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-500">
            Secure login for authorized users only
          </p>
        </div>
      </div>
    </div>
  );
}
