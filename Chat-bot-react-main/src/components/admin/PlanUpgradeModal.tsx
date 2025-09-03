import React, { useState } from "react";
import { Modal, Button, Card, Row, Col, message } from "antd";
import { CheckOutlined, CloseOutlined } from "@ant-design/icons";
import { requestPlanUpgrade } from "../../api/post";

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
  name: string;
  icon: string;
  price: number | null;
  subtitle: string;
  maxAgents: number | string;
  features: PlanFeature[];
  bgColor: string;
  textColor: string;
  borderColor: string;
  buttonColor: string;
}

const plans: Plan[] = [
  {
    name: "Bronze",
    icon: "🥉",
    price: 2000,
    subtitle: "Basic Plan",
    maxAgents: 2,
    bgColor: "bg-gradient-to-br from-amber-50 to-orange-100",
    textColor: "text-amber-800",
    borderColor: "border-amber-300",
    buttonColor: "bg-amber-600 hover:bg-amber-700",
    features: [
      { text: "Basic chatbot (FAQ + RAG-lite)", included: true },
      { text: "Basic admin dashboard analytics", included: true },
      { text: "Custom chatbot branding (logo & color)", included: true },
      { text: "No multi-chatbot support", included: false },
      { text: "No priority support", included: false },
    ],
  },
  {
    name: "Silver",
    icon: "🥈",
    price: 4000,
    subtitle: "Enhanced Plan",
    maxAgents: 4,
    bgColor: "bg-gradient-to-br from-gray-50 to-slate-100",
    textColor: "text-slate-700",
    borderColor: "border-slate-300",
    buttonColor: "bg-slate-600 hover:bg-slate-700",
    features: [
      { text: "Everything in Bronze, plus:", included: true },
      { text: "Multi-chatbot support (up to 2 bots)", included: true },
      {
        text: "Advanced analytics (conversation history, CSV export)",
        included: true,
      },
      { text: "Agent performance tracking (basic KPIs)", included: true },
      { text: "No API access / advanced integrations", included: false },
    ],
  },
  {
    name: "Gold",
    icon: "🥇",
    price: 6000,
    subtitle: "Professional Plan",
    maxAgents: 6,
    bgColor: "bg-gradient-to-br from-yellow-50 to-amber-100",
    textColor: "text-yellow-800",
    borderColor: "border-yellow-400",
    buttonColor: "bg-yellow-600 hover:bg-yellow-700",
    features: [
      { text: "Everything in Silver, plus:", included: true },
      { text: "Multi-chatbot support (up to 5 bots)", included: true },
      { text: "Priority support (email + chat)", included: true },
      { text: "Custom domains for company chatbots", included: true },
      { text: "Webhooks for chatbot events", included: true },
      { text: "No white-labeling", included: false },
    ],
  },
  {
    name: "Platinum",
    icon: "💎",
    price: 8000,
    subtitle: "Premium Plan",
    maxAgents: 10,
    bgColor: "bg-gradient-to-br from-blue-50 to-indigo-100",
    textColor: "text-blue-800",
    borderColor: "border-blue-400",
    buttonColor: "bg-blue-600 hover:bg-blue-700",
    features: [
      { text: "Everything in Gold, plus:", included: true },
      { text: "Full API access", included: true },
      { text: "CRM integrations (HubSpot, Zoho, etc.)", included: true },
      { text: "White-label option (remove our logo)", included: true },
      { text: "Role-based access control", included: true },
      { text: "No dedicated account manager", included: false },
    ],
  },
  {
    name: "Diamond",
    icon: "💠",
    price: 10000,
    subtitle: "Enterprise Plan",
    maxAgents: "20+",
    bgColor: "bg-gradient-to-br from-purple-50 to-pink-100",
    textColor: "text-purple-800",
    borderColor: "border-purple-400",
    buttonColor: "bg-purple-600 hover:bg-purple-700",
    features: [
      { text: "Everything in Platinum, plus:", included: true },
      { text: "Dedicated account manager", included: true },
      { text: "SLA-backed support (24/7)", included: true },
      {
        text: "AI model customization (fine-tuning with company data)",
        included: true,
      },
      { text: "Unlimited chatbots", included: true },
      { text: "Enterprise-level analytics dashboard", included: true },
      {
        text: "Custom deployment (on-premise / private cloud)",
        included: true,
      },
    ],
  },
  {
    name: "Custom",
    icon: "⚙️",
    price: null,
    subtitle: "Tailored Solution",
    maxAgents: "As per need",
    bgColor: "bg-gradient-to-br from-emerald-50 to-teal-100",
    textColor: "text-emerald-800",
    borderColor: "border-emerald-400",
    buttonColor: "bg-emerald-600 hover:bg-emerald-700",
    features: [
      { text: "Mix & match features", included: true },
      { text: "Tailored integrations & support", included: true },
      { text: "Pricing negotiable (contact sales)", included: true },
      { text: "Custom deployment options", included: true },
      { text: "Dedicated project manager", included: true },
    ],
  },
];

export default function PlanUpgradeModal({
  isOpen,
  onClose,
  currentPlan,
}: PlanUpgradeModalProps) {
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handlePlanSelect = (planName: string) => {
    if (planName.toLowerCase() === currentPlan.toLowerCase()) {
      message.info("You are already on this plan");
      return;
    }
    setSelectedPlan(planName);
    setShowConfirmation(true);
  };

  const handleConfirmUpgrade = async () => {
    try {
      await requestPlanUpgrade({
        requested_plan: selectedPlan || "",
        reason: `Upgrade request from ${currentPlan} to ${selectedPlan}`,
      });
      message.success(
        `Upgrade request for ${selectedPlan} plan has been sent to administrator for approval.`
      );
      setShowConfirmation(false);
      onClose();
    } catch {
      message.error("Failed to submit upgrade request. Please try again.");
    }
  };

  const handleCancelConfirmation = () => {
    setShowConfirmation(false);
    setSelectedPlan(null);
  };

  const renderPlanCard = (plan: Plan) => {
    const isCurrentPlan = plan.name.toLowerCase() === currentPlan.toLowerCase();

    return (
      <Col xs={24} sm={12} lg={8} key={plan.name}>
        <Card
          className={`h-full ${plan.bgColor} ${
            plan.borderColor
          } border-2 hover:shadow-lg transition-all duration-300 ${
            isCurrentPlan ? "ring-2 ring-blue-500" : ""
          }`}
          hoverable={!isCurrentPlan}
          onClick={() => !isCurrentPlan && handlePlanSelect(plan.name)}
          styles={{ body: { padding: "16px", height: "100%" } }}
        >
          <div className="text-center mb-3">
            <div className="text-3xl mb-1">{plan.icon}</div>
            <h3 className={`text-lg font-bold ${plan.textColor}`}>
              {plan.name}
            </h3>
            <p className={`text-xs ${plan.textColor} opacity-80`}>
              {plan.subtitle}
            </p>
            <div className={`text-xl font-bold ${plan.textColor} mt-1`}>
              {plan.price
                ? `₨${plan.price.toLocaleString()} / month`
                : "Contact Sales"}
            </div>
          </div>

          <div className="mb-3">
            <div
              className={`text-center p-1.5 rounded-lg ${plan.textColor} bg-white bg-opacity-50`}
            >
              <span className="font-semibold text-sm">
                👥 Max Agents: {plan.maxAgents}
              </span>
            </div>
          </div>

          <div className="space-y-1.5 mb-3">
            {plan.features.map((feature, index) => (
              <div
                key={`${plan.name}-feature-${index}`}
                className="flex items-start space-x-2"
              >
                {feature.included ? (
                  <CheckOutlined className="text-green-600 mt-0.5 flex-shrink-0 text-xs" />
                ) : (
                  <CloseOutlined className="text-red-500 mt-0.5 flex-shrink-0 text-xs" />
                )}
                <span
                  className={`text-xs ${
                    feature.included ? "text-gray-700" : "text-gray-500"
                  }`}
                >
                  {feature.text}
                </span>
              </div>
            ))}
          </div>

          {isCurrentPlan && (
            <div className="mt-3 text-center">
              <Button disabled className="w-full text-sm">
                Current Plan
              </Button>
            </div>
          )}

          {!isCurrentPlan && (
            <div className="mt-3 text-center">
              <Button
                type="primary"
                className={`w-full ${plan.buttonColor} border-none text-white font-semibold text-sm`}
                onClick={() => handlePlanSelect(plan.name)}
              >
                Choose {plan.name}
              </Button>
            </div>
          )}
        </Card>
      </Col>
    );
  };

  return (
    <>
      <Modal
        title={
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-800">
              Upgrade Your Plan
            </h2>
            <p className="text-gray-600">
              Choose the perfect plan for your business needs
            </p>
          </div>
        }
        open={isOpen}
        onCancel={onClose}
        footer={null}
        width={1600}
        style={{ top: 10 }}
        styles={{
          body: {
            maxHeight: "85vh",
            overflowY: "auto",
            padding: "16px",
          },
        }}
        className="plan-upgrade-modal"
      >
        <div className="pb-2">
          <Row gutter={[12, 12]}>{plans.map(renderPlanCard)}</Row>
        </div>
      </Modal>

      {/* Confirmation Modal */}
      <Modal
        title="Confirm Plan Upgrade"
        open={showConfirmation}
        onOk={handleConfirmUpgrade}
        onCancel={handleCancelConfirmation}
        okText="Yes, Upgrade"
        cancelText="Cancel"
        okButtonProps={{
          className:
            "bg-blue-600 border-blue-600 hover:bg-blue-700 hover:border-blue-700",
        }}
      >
        <div className="py-4">
          <p className="text-lg mb-3">
            Do you want to upgrade to the <strong>{selectedPlan}</strong> plan?
          </p>
          <p className="text-gray-600">
            Your upgrade request will be sent to the administrator for approval.
          </p>
        </div>
      </Modal>
    </>
  );
}
