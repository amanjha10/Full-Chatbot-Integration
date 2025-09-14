import React, { useState, useEffect } from "react";
import { Modal, Button, message } from "antd";
import { CheckOutlined, CloseOutlined, LoadingOutlined } from "@ant-design/icons";
import { axiosClient } from "../../config/axiosConfig";
import "./PlanUpgradeModal.css";

interface PlanUpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentPlan: string;
}

interface PlanFeature {
  text: string;
  included: boolean;
}

interface Plan {
  id: number;
  name: string;
  for_whom: string;
  price: number | null;
  max_agents: string;
  features_line: string;
  css_meta: {
    gradient: string;
    text_color: string;
    border_color: string;
    button_color: string;
    shine_color: string;
  };
  icon: string;
  sort_order: number;
}

interface CompanyPlanInfo {
  company_id: string;
  current_plan: string;
  requested_plan: string | null;
  has_pending_request: boolean;
}

// Using axiosClient with configured baseURL from environment

const PlanUpgradeModal: React.FC<PlanUpgradeModalProps> = ({
  isOpen,
  onClose,
  currentPlan,
}) => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [companyPlanInfo, setCompanyPlanInfo] = useState<CompanyPlanInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);

  // Fetch plans from Admin API (accessible to Admin users)
  const fetchPlans = async () => {
    try {
      setLoading(true);
      const response = await axiosClient.get("/chatbot/admin/plans/");
      setPlans(response.data);
    } catch (error) {
      console.error("Error fetching plans:", error);
      message.error("Failed to load plans");
    } finally {
      setLoading(false);
    }
  };

  // Check for pending upgrade requests using the dedicated admin endpoint
  const checkPendingRequests = async () => {
    try {
      // Use the dedicated endpoint for admins to check their own status
      const response = await axiosClient.get("/admin-dashboard/my-plan-upgrade-status/");

      if (response.data.has_pending_request) {
        return {
          requested_plan: response.data.requested_plan,
          ...response.data.request_details
        };
      }

      return null;
    } catch (error: any) {
      console.error("Error checking pending requests:", error);
      return null;
    }
  };

  // Fetch company plan info from user profile API (gets current user's company)
  const fetchCompanyPlanInfo = async () => {
    try {
      // First get user profile to get company_id and role
      const profileResponse = await axiosClient.get("/auth/profile/");

      const userCompanyId = profileResponse.data.company_id;
      const userRole = profileResponse.data.role;
      setUserRole(userRole);

      // For SuperAdmin, don't fetch subscription info
      if (userRole === 'SUPERADMIN') {
        setCompanyPlanInfo({
          company_id: userCompanyId,
          current_plan: "Unlimited",
          requested_plan: null,
          has_pending_request: false,
        });
        return;
      }

      // For Admin users, use the profile data directly (more reliable)
      // The profile already contains current_plan information
      const currentPlan = profileResponse.data.current_plan?.name || "Silver";

      // Set initial company plan info
      setCompanyPlanInfo({
        company_id: userCompanyId,
        current_plan: currentPlan,
        requested_plan: null,
        has_pending_request: false,
      });

      // Check for pending requests after setting initial info
      const pendingRequest = await checkPendingRequests();

      if (pendingRequest) {
        setCompanyPlanInfo({
          company_id: userCompanyId,
          current_plan: currentPlan,
          requested_plan: pendingRequest.requested_plan,
          has_pending_request: true,
        });
      }

      // Show info message if there's a pending request
      if (pendingRequest) {
        message.info(
          `You have a pending upgrade request to ${pendingRequest.requested_plan} plan. Please wait for approval.`,
          5 // Show for 5 seconds
        );
      }
    } catch (error) {
      console.error("Error fetching company plan info:", error);
      // Set fallback data if API fails
      setCompanyPlanInfo({
        company_id: "SPE001",
        current_plan: currentPlan || "Silver",
        requested_plan: null,
        has_pending_request: false,
      });
    }
  };

  // Load data when modal opens
  useEffect(() => {
    if (isOpen) {
      fetchPlans();
      fetchCompanyPlanInfo();
    }
  }, [isOpen]);

  // Handle plan upgrade request
  const handlePlanUpgrade = async (planId: number, planName: string) => {
    try {
      setRequesting(true);
      setSelectedPlan(planName);

      console.log("🚀 Requesting plan upgrade:", {
        planId,
        planName,
        currentPlan,
        requestData: {
          requested_plan: planName,
          reason: `Upgrade request from ${currentPlan} to ${planName}`,
        }
      });

      // Use the admin dashboard API endpoint that works
      const response = await axiosClient.post(
        "/admin-dashboard/request-plan-upgrade/",
        {
          requested_plan: planName,
          reason: `Upgrade request from ${currentPlan} to ${planName}`,
        }
      );

      console.log("✅ Plan upgrade response:", response.data);

      if (response.data.message) {
        message.success(response.data.message);
        await fetchCompanyPlanInfo(); // Refresh company plan info
        onClose();
      }
    } catch (error: any) {
      console.error("❌ Error requesting plan upgrade:", error);
      console.error("❌ Error response data:", error.response?.data);

      // Handle specific error cases
      if (error.response?.status === 400) {
        const errorData = error.response.data;
        console.log("🔍 400 Error details:", errorData);

        if (errorData.error && errorData.existing_request) {
          // Handle pending request error
          const existingRequest = errorData.existing_request;
          message.warning(
            `You already have a pending upgrade request to ${existingRequest.requested_plan} plan. Please wait for approval or contact support.`
          );
        } else if (errorData.error) {
          // Handle other 400 errors with specific error message
          message.error(errorData.error);
        } else {
          message.error("Invalid request. Please check your input.");
        }
      } else if (error.response?.status === 403) {
        message.error("You don't have permission to request plan upgrades.");
      } else if (error.response?.status === 401) {
        message.error("Please login again to continue.");
      } else {
        const errorMessage = error.response?.data?.error || error.message || "Failed to submit upgrade request";
        message.error(errorMessage);
      }
    } finally {
      setRequesting(false);
      setSelectedPlan(null);
    }
  };

  // Handle cancel pending request
  const handleCancelRequest = async () => {
    try {
      setRequesting(true);

      console.log("🚀 Cancelling plan upgrade request...");
      const response = await axiosClient.post("/admin-dashboard/cancel-plan-upgrade/");

      console.log("✅ Cancel response:", response.data);
      message.success(response.data.message || "Plan upgrade request cancelled successfully!");

      // Refresh company plan info to update UI
      await fetchCompanyPlanInfo();
    } catch (error: any) {
      console.error("❌ Error cancelling plan upgrade:", error);
      const errorMessage = error.response?.data?.error || "Failed to cancel upgrade request";
      message.error(errorMessage);
    } finally {
      setRequesting(false);
    }
  };

  // Get plan status
  const getPlanStatus = (planName: string) => {
    if (!companyPlanInfo) return "available";

    if (companyPlanInfo.current_plan === planName) {
      return "current";
    }

    if (companyPlanInfo.has_pending_request && companyPlanInfo.requested_plan === planName) {
      return "requested";
    }

    return "available";
  };

  // Get plan CSS class name
  const getPlanClassName = (planName: string) => {
    const classMap: { [key: string]: string } = {
      'Bronze': 'bronze',
      'Silver': 'silver',
      'Gold': 'gold',
      'Platinum': 'platinum',
      'Diamond': 'diamond',
      'Custom': 'custom'
    };
    return classMap[planName] || 'bronze';
  };

  // Get button text and style based on plan status
  const getButtonConfig = (planName: string) => {
    // Disable all upgrades for SuperAdmin users
    if (userRole === 'SUPERADMIN') {
      return {
        text: "Unlimited Access",
        disabled: true,
        type: "default" as const,
        style: { backgroundColor: "#52c41a", borderColor: "#52c41a", color: "white" }
      };
    }

    const status = getPlanStatus(planName);

    switch (status) {
      case "current":
        return {
          text: "Current Plan",
          disabled: true,
          type: "default" as const,
          style: { backgroundColor: "#52c41a", borderColor: "#52c41a", color: "white" }
        };
      case "requested":
        return {
          text: "Requested",
          disabled: true,
          type: "default" as const,
          style: { backgroundColor: "#faad14", borderColor: "#faad14", color: "white" }
        };
      default:
        // For other plans, always show "Upgrade" (don't disable them)
        return {
          text: "Upgrade",
          disabled: false,
          type: "primary" as const,
          style: {}
        };
    }
  };

  if (loading) {
    return (
      <Modal
        title="Plan Upgrade"
        open={isOpen}
        onCancel={onClose}
        footer={null}
        width={1200}
        centered
      >
        <div style={{ textAlign: "center", padding: "50px" }}>
          <LoadingOutlined style={{ fontSize: 24 }} spin />
          <p style={{ marginTop: 16 }}>Loading plans...</p>
        </div>
      </Modal>
    );
  }

  return (
    <Modal
      title={
        <div className="gradient-text" style={{ textAlign: "center", fontSize: "24px", fontWeight: "bold" }}>
          🚀 Upgrade Your Plan
        </div>
      }
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={1400}
      centered
      className="plan-upgrade-modal"
      styles={{
        body: { padding: "20px" }
      }}
    >
      <div style={{ marginBottom: "20px", textAlign: "center" }}>
        <p style={{ fontSize: "16px", color: "#666" }}>
          Choose the perfect plan for your business needs
        </p>

        {/* Show message for SuperAdmin users */}
        {userRole === 'SUPERADMIN' && (
          <div style={{
            backgroundColor: "#f6ffed",
            border: "1px solid #b7eb8f",
            borderRadius: "6px",
            padding: "12px",
            margin: "16px 0",
            textAlign: "center"
          }}>
            <span style={{ color: "#52c41a", fontWeight: "600" }}>
              🎉 You have SuperAdmin access with unlimited features! No plan upgrade needed.
            </span>
          </div>
        )}

        {companyPlanInfo?.has_pending_request && (
          <div className="pending-request-banner" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ color: "#fa8c16", fontWeight: "600" }}>
              ⏳ You have a pending upgrade request for <strong>{companyPlanInfo.requested_plan}</strong>
            </span>
            <Button
              type="default"
              size="small"
              danger
              loading={requesting}
              onClick={handleCancelRequest}
              style={{
                marginLeft: "16px",
                borderRadius: "6px",
                fontWeight: "600"
              }}
            >
              Cancel Request
            </Button>
          </div>
        )}
      </div>

      <div className="plan-grid-container">
        {plans.map((plan) => {
          const buttonConfig = getButtonConfig(plan.name);
          const isRequesting = requesting && selectedPlan === plan.name;

          return (
              <div
                key={plan.id}
                className={`shine-card ${getPlanClassName(plan.name)}`}
                style={{
                  color: plan.css_meta.text_color.includes('white') ? 'white' : '#333',
                }}
              >
                {/* Shine Effects */}
                <div className="shine-overlay"></div>
                <div className="auto-shine"></div>

                {/* Card Content */}
                <div className="plan-card-content" style={{ padding: "20px" }}>
                {/* Plan header */}
                <div className="plan-header">
                  <h3 className="plan-title">
                    {plan.name}
                  </h3>
                  <p className="plan-subtitle">
                    {plan.for_whom}
                  </p>
                  <div className={`plan-price ${plan.price ? '' : 'plan-price-custom'}`}>
                    {plan.price ? `₹${plan.price}` : "Custom"}
                  </div>
                  <div className="plan-agents">
                    👥 {plan.max_agents} agents
                  </div>
                </div>

                {/* Features */}
                <div className="plan-features-container">
                  <div className="plan-features">
                    <div className="plan-feature">
                      <CheckOutlined style={{ color: "#52c41a" }} />
                      <span>{plan.features_line}</span>
                    </div>
                  </div>
                </div>

                {/* Action button */}
                <div className="plan-button-container">
                  <Button
                    {...buttonConfig}
                    loading={isRequesting}
                    onClick={() => handlePlanUpgrade(plan.id, plan.name)}
                    block
                    className={`plan-status-${getPlanStatus(plan.name)}`}
                    style={buttonConfig.style}
                  >
                    {buttonConfig.text}
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Modal>
  );
};

export default PlanUpgradeModal;