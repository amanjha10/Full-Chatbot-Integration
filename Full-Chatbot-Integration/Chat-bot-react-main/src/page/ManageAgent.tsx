import { useState } from "react";
import Card from "../components/dashboard/Card";
import AddAgent from "../components/ManageAgent/AddAgent";
import ViewAgent from "../components/ManageAgent/ViewAgent";
import AppDeleteModal from "../components/AppDeleteModal";
import PlanUpgradeModal from "../components/admin/PlanUpgradeModal";
import useSWR from "swr";
import { useColumnsAgentList } from "../TableColumns/useColumnsAgentList";
import AppTable from "../share/form/AppTable";
import { Button, type MenuProps, Alert, Badge, Tooltip } from "antd";
import { IoEyeOutline } from "react-icons/io5";
import { RiResetLeftFill } from "react-icons/ri";
import { MdDeleteOutline } from "react-icons/md";
import { FiPlus } from "react-icons/fi";
import { axiosClient } from "../config/axiosConfig";
import { useMessageContext } from "../context-provider/MessageProvider";
import { useAgentLimits } from "../hooks/useAgentLimits";
import type { AgentListType } from "../type/admin/AdminDataType";

export default function ManageAgent() {
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState<boolean>(false);
  const [isDeleteModalOpen, setIsDeleteModal] = useState<boolean>(false);
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState<boolean>(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentListType | null>(
    null
  );
  const [loading, setLoading] = useState<boolean>(false);
  const { messageApi } = useMessageContext();
  const { data, isLoading, mutate } = useSWR("/admin-dashboard/list-agents/");
  const {
    limits,
    canCreateAgent,
    currentUsage,
    planName,
    showUpgradeMessage,
    fetchLimits,
  } = useAgentLimits();

  const handleOpenModal = () => {
    if (!canCreateAgent) {
      showUpgradeMessage();
      return;
    }
    setIsModalOpen(true);
  };
  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  const handleAgentCreated = () => {
    // Refresh both agents list and limits after successful creation
    mutate();
    fetchLimits();
  };
  const handleOpenViewModal = (agent: AgentListType) => {
    setSelectedAgent(agent);
    setIsViewModalOpen(true);
  };
  const handleCloseViewModal = () => {
    setIsViewModalOpen(false);
    setSelectedAgent(null);
  };
  const handleOpenDeleteModal = () => {
    setIsDeleteModal(true);
  };
  const handleCloseDeleteModal = () => {
    setIsDeleteModal(false);
    setSelectedAgent(null);
  };

  const handleDeleteAgent = async () => {
    if (!selectedAgent) return;

    setLoading(true);
    try {
      await axiosClient.delete(
        `/admin-dashboard/delete-agent/${selectedAgent.id}/`
      );
      messageApi.success("Agent deleted successfully");
      mutate();
      handleCloseDeleteModal();
    } catch (error: unknown) {
      const err = error as {
        response?: { data?: { error?: string } };
        message?: string;
      };
      messageApi.error(
        err?.response?.data?.error || err?.message || "Failed to delete agent"
      );
    } finally {
      setLoading(false);
    }
  };
  const getItemMenu = (row: AgentListType): MenuProps["items"] => [
    {
      label: "View",
      key: "1",
      icon: <IoEyeOutline size={17} />,
      onClick: () => {
        handleOpenViewModal(row);
      },
    },
    {
      label: "Reset Password",
      key: "2",
      icon: <RiResetLeftFill size={17} />,
      onClick: async () => {
        try {
          const response = await axiosClient.post(
            "/admin-dashboard/reset-agent-password/",
            {
              agent_id: row?.id,
            }
          );

          const { new_password } = response.data;
          messageApi.success(
            `Password reset successfully!
            New Password: ${new_password}
            Agent must use this password for first login.`
          );
          mutate();
        } catch (error: unknown) {
          const err = error as {
            response?: { data?: { error?: string } };
            message?: string;
          };
          messageApi.error(
            err?.response?.data?.error ||
              err?.message ||
              "Failed to reset password"
          );
        }
      },
    },
    {
      label: "Delete",
      key: "3",
      icon: <MdDeleteOutline size={17} />,
      danger: true,
      onClick: () => {
        setSelectedAgent(row);
        handleOpenDeleteModal();
      },
    },
  ];

  const getTagColor = (tagName: string) => {
    switch (tagName) {
      case "AVAILABLE": {
        return "#155724";
      }
      case "OFFLINE": {
        return "#000000";
      }
      default:
        return "#ff0000";
    }
  };
  const { columns } = useColumnsAgentList({ getTagColor, getItemMenu });

  return (
    <div className="pt-4 space-y-5">
      <div className="flex justify-between items-center">
        <h2 className="font-bold text-2xl">Agent Management</h2>
        {/* Plan Usage Info */}
        {currentUsage && planName && (
          <div className="flex items-center gap-3">
            <Badge
              count={currentUsage}
              color={canCreateAgent ? "#52c41a" : "#f5222d"}
              style={{
                backgroundColor: canCreateAgent ? "#52c41a" : "#f5222d",
              }}
            />
            <span className="text-sm text-gray-600">{planName} Plan</span>
          </div>
        )}
      </div>

      {/* Upgrade Alert */}
      {limits?.upgrade_needed && (
        <Alert
          message={limits?.is_cancelled ? "Subscription Cancelled" : "Agent Limit Reached"}
          description={
            <div className="flex justify-between items-center">
              <span>
                {limits?.is_cancelled
                  ? `Your subscription was cancelled. Please upgrade your plan.`
                  : `Agent limit reached. Your ${limits.plan_name} plan allows maximum ${limits.max_allowed} agents. Please upgrade to add more agents.`
                }
              </span>
              <Button
                type="primary"
                size="small"
                className={`ml-4 ${
                  limits?.is_cancelled
                    ? "bg-red-500 border-red-500 hover:bg-red-600 hover:border-red-600"
                    : "bg-yellow-500 border-yellow-500 hover:bg-yellow-600 hover:border-yellow-600"
                }`}
                onClick={() => setIsUpgradeModalOpen(true)}
              >
                Upgrade
              </Button>
            </div>
          }
          type={limits?.is_cancelled ? "error" : "warning"}
          showIcon
          closable
        />
      )}

      <div className="grid grid-cols-2 md:grid-cols-3  xl:grid-cols-4 gap-10 ">
        <Card title="Session Pending" count={8} />
        <Card title="Session Pending" count={8} />
        <Card title="Session Pending" count={8} />
        <Card title="Session Pending" count={8} />
      </div>
      <div className="flex justify-between items-center">
        <h6 className="font-bold text-xl">Agent Table</h6>
        <Tooltip
          title={
            !canCreateAgent
              ? `Agent limit reached (${currentUsage}). ${
                  limits?.suggestion || "Upgrade your plan to add more agents"
                }`
              : `Add new agent (${currentUsage} used)`
          }
        >
          <Button
            type="primary"
            className={`${canCreateAgent ? "!bg-yellow" : "!bg-gray-400"}`}
            icon={<FiPlus size={15} />}
            onClick={handleOpenModal}
            disabled={!canCreateAgent}
          >
            Add Agent
          </Button>
        </Tooltip>
      </div>
      <AppTable columns={columns} dataSource={data} loading={isLoading} />
      {isModalOpen && (
        <AddAgent
          mutate={handleAgentCreated}
          setLoading={setLoading}
          loading={loading}
          isModalOpen={isModalOpen}
          onCancel={handleCloseModal}
        />
      )}
      {isViewModalOpen && (
        <ViewAgent
          isOpen={isViewModalOpen}
          onClose={handleCloseViewModal}
          agent={selectedAgent}
          onUpdate={() => {
            mutate();
            handleCloseViewModal();
          }}
        />
      )}
      {isDeleteModalOpen && (
        <AppDeleteModal
          isDeleteOpenModal={isDeleteModalOpen}
          handleCancel={handleCloseDeleteModal}
          onDelete={handleDeleteAgent}
          loading={loading}
          name={selectedAgent?.name}
        />
      )}
      {isUpgradeModalOpen && (
        <PlanUpgradeModal
          isOpen={isUpgradeModalOpen}
          onClose={() => setIsUpgradeModalOpen(false)}
          currentPlan={limits?.plan_name || "Unknown"}
        />
      )}
    </div>
  );
}
