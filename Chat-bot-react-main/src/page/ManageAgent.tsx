import { useState } from "react";
import Card from "../components/dashboard/Card";
import AgentTable from "../components/ManageAgent/AgentTable";
import AddAgent from "../components/ManageAgent/AddAgent";
import ViewAgent from "../components/ManageAgent/ViewAgent";
import AppDeleteModal from "../components/AppDeleteModal";
import useSWR from "swr";
import { useColumnsAgentList } from "../TableColumns/useColumnsAgentList";
import AppTable from "../share/form/AppTable";
import { Button, type MenuProps } from "antd";
import { IoEyeOutline } from "react-icons/io5";
import { RiResetLeftFill } from "react-icons/ri";
import { MdDeleteOutline } from "react-icons/md";
import { FiPlus } from "react-icons/fi";
import { resetPassword } from "../api/post";
import { useMessageContext } from "../context-provider/MessageProvider";
import type { AgentListType } from "../type/admin/AdminDataType";

export default function ManageAgent() {
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState<boolean>(false);
  const [isDeleteModalOpen, setIsDeleteModal] = useState<boolean>(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentListType | null>(
    null
  );
  const [loading, setLoading] = useState<boolean>(false);
  const { messageApi } = useMessageContext();
  const { data, isLoading, mutate } = useSWR("/admin-dashboard/list-agents/");
  const handleOpenModal = () => {
    setIsModalOpen(true);
  };
  const handleCloseModal = () => {
    setIsModalOpen(false);
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
    } catch (error: any) {
      messageApi.error(
        error?.response?.data?.error || "Failed to delete agent"
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
        } catch (error: any) {
          messageApi.error(
            error?.response?.data?.error || "Failed to reset password"
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
      <h2 className="font-bold text-2xl">Agent Management</h2>
      <div className="grid grid-cols-2 md:grid-cols-3  xl:grid-cols-4 gap-10 ">
        <Card title="Session Pending" count={8} />
        <Card title="Session Pending" count={8} />
        <Card title="Session Pending" count={8} />
        <Card title="Session Pending" count={8} />
      </div>
      <div className="flex justify-between">
        <h6 className="font-bold text-xl">Agent Table</h6>
        <Button
          type="primary"
          className="!bg-yellow"
          icon={<FiPlus size={15} />}
          onClick={handleOpenModal}
        >
          Agent
        </Button>
      </div>
      <AppTable columns={columns} dataSource={data} loading={isLoading} />
      {isModalOpen && (
        <AddAgent
          mutate={mutate}
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
          title={`Delete Agent: ${selectedAgent?.name}`}
          description={`Are you sure you want to delete agent "${selectedAgent?.name}"? This action cannot be undone.`}
        />
      )}
    </div>
  );
}
