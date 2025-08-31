import {
  Modal,
  Tag,
  Button,
  Typography,
  Divider,
  Form,
  Input,
  message,
} from "antd";
import { IoClose } from "react-icons/io5";
import { MdEdit, MdSave, MdCancel } from "react-icons/md";
import { useState } from "react";
import { axiosClient } from "../../config/axiosConfig";
import type { AgentListType } from "../../type/admin/AdminDataType";

const { Title, Text } = Typography;

interface ViewAgentProps {
  isOpen: boolean;
  onClose: () => void;
  agent: AgentListType | null;
  onUpdate?: () => void;
}

export default function ViewAgent({
  isOpen,
  onClose,
  agent,
  onUpdate,
}: ViewAgentProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  if (!agent) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case "PENDING":
        return "blue";
      case "AVAILABLE":
        return "green";
      case "BUSY":
        return "orange";
      case "OFFLINE":
        return "red";
      default:
        return "default";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "PENDING":
        return "Pending First Login";
      case "AVAILABLE":
        return "Available";
      case "BUSY":
        return "Busy";
      case "OFFLINE":
        return "Offline";
      default:
        return status;
    }
  };

  const handleEdit = () => {
    form.setFieldsValue({
      name: agent.name,
      phone: agent.phone,
      email: agent.email,
      specialization: agent.specialization,
    });
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    form.resetFields();
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      await axiosClient.put(
        `/admin-dashboard/update-agent/${agent.id}/`,
        values
      );

      message.success("Agent updated successfully");
      setIsEditing(false);
      onUpdate?.();
    } catch (error: any) {
      message.error(error?.response?.data?.error || "Failed to update agent");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={
        <div className="flex items-center justify-between">
          <Title level={4} className="!mb-0">
            Agent Details
          </Title>
          <div className="flex items-center gap-2">
            {!isEditing ? (
              <Button
                type="primary"
                icon={<MdEdit size={16} />}
                onClick={handleEdit}
                size="small"
              >
                Edit
              </Button>
            ) : (
              <>
                <Button
                  type="primary"
                  icon={<MdSave size={16} />}
                  onClick={handleSave}
                  loading={loading}
                  size="small"
                >
                  Save
                </Button>
                <Button
                  icon={<MdCancel size={16} />}
                  onClick={handleCancel}
                  size="small"
                >
                  Cancel
                </Button>
              </>
            )}
            <Button
              type="text"
              icon={<IoClose size={20} />}
              onClick={onClose}
              className="!p-1"
            />
          </div>
        </div>
      }
      open={isOpen}
      onCancel={onClose}
      footer={null}
      width={1000}
      closable={false}
    >
      <Divider className="!mt-4 !mb-6" />

      <div className="grid grid-cols-4 gap-6">
        {/* Basic Information */}
        <div className="space-y-4">
          <Title level={5} className="!mb-4 text-gray-700 border-b pb-2">
            Basic Information
          </Title>
          {isEditing ? (
            <Form form={form} layout="vertical">
              <div className="grid grid-cols-2 gap-4">
                <Form.Item
                  label="Name"
                  name="name"
                  rules={[{ required: true, message: "Name is required" }]}
                >
                  <Input placeholder="Enter name" />
                </Form.Item>
                <Form.Item
                  label="Phone"
                  name="phone"
                  rules={[{ required: true, message: "Phone is required" }]}
                >
                  <Input placeholder="Enter phone number" />
                </Form.Item>
                <Form.Item
                  label="Email"
                  name="email"
                  rules={[
                    { required: true, message: "Email is required" },
                    { type: "email", message: "Invalid email format" },
                  ]}
                >
                  <Input placeholder="Enter email" />
                </Form.Item>
                <Form.Item
                  label="Specialization"
                  name="specialization"
                  rules={[
                    { required: true, message: "Specialization is required" },
                  ]}
                >
                  <Input placeholder="Enter specialization" />
                </Form.Item>
              </div>
            </Form>
          ) : (
            <div className="space-y-3">
              <div>
                <Text type="secondary" className="text-sm">
                  Name
                </Text>
                <div>
                  <Text strong>{agent.name}</Text>
                </div>
              </div>
              <div>
                <Text type="secondary" className="text-sm">
                  Email
                </Text>
                <div>
                  <Text copyable>{agent.email}</Text>
                </div>
              </div>
              <div>
                <Text type="secondary" className="text-sm">
                  Phone
                </Text>
                <div>
                  <Text>{agent.phone || "Not provided"}</Text>
                </div>
              </div>
              <div>
                <Text type="secondary" className="text-sm">
                  Specialization
                </Text>
                <div>
                  <Text>{agent.specialization || "General Support"}</Text>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Login Credentials */}
        <div className="space-y-4">
          <Title level={5} className="!mb-4 text-gray-700 border-b pb-2">
            Login Credentials
          </Title>
          <div className="space-y-3">
            <div>
              <Text type="secondary" className="text-sm">
                Username/Email
              </Text>
              <div>
                <Text copyable code className="text-xs">
                  {agent.email}
                </Text>
              </div>
            </div>
            <div>
              <Text type="secondary" className="text-sm">
                Generated Password
              </Text>
              <div>
                <Text copyable code className="text-xs">
                  {agent.generated_password || "Contact admin"}
                </Text>
              </div>
              <Text type="secondary" className="text-xs">
                * Used for first login only
              </Text>
            </div>
            <div>
              <Text type="secondary" className="text-sm">
                Login Status
              </Text>
              <div>
                <Tag
                  color={agent.is_first_login ? "orange" : "green"}
                  className="text-xs"
                >
                  {agent.is_first_login
                    ? "First Login Required"
                    : "Setup Complete"}
                </Tag>
              </div>
            </div>
          </div>
        </div>

        {/* Status Information */}
        <div className="space-y-4">
          <Title level={5} className="!mb-4 text-gray-700 border-b pb-2">
            Status Information
          </Title>
          <div className="space-y-3">
            <div>
              <Text type="secondary" className="text-sm">
                Current Status
              </Text>
              <div>
                <Tag color={getStatusColor(agent.status)} className="text-xs">
                  {getStatusText(agent.status)}
                </Tag>
              </div>
            </div>
            <div>
              <Text type="secondary" className="text-sm">
                Last Active
              </Text>
              <div>
                <Text className="text-sm">
                  {agent.formatted_last_active || "Never"}
                </Text>
              </div>
            </div>
            <div>
              <Text type="secondary" className="text-sm">
                Company ID
              </Text>
              <div>
                <Text code className="text-xs">
                  {agent.company_id}
                </Text>
              </div>
            </div>
          </div>
        </div>

        {/* Account Information */}
        <div className="space-y-4">
          <Title level={5} className="!mb-4 text-gray-700 border-b pb-2">
            Account Information
          </Title>
          <div className="space-y-3">
            <div>
              <Text type="secondary" className="text-sm">
                Agent ID
              </Text>
              <div>
                <Text code className="text-xs">
                  #{agent.id}
                </Text>
              </div>
            </div>
            <div>
              <Text type="secondary" className="text-sm">
                Created Date
              </Text>
              <div>
                <Text className="text-sm">
                  {new Date().toLocaleDateString()}
                </Text>
              </div>
            </div>
            <div>
              <Text type="secondary" className="text-sm">
                Setup Status
              </Text>
              <div>
                <Tag
                  color={agent.status === "PENDING" ? "orange" : "green"}
                  className="text-xs"
                >
                  {agent.status === "PENDING"
                    ? "Pending Setup"
                    : "Setup Complete"}
                </Tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <Divider className="!mt-6 !mb-4" />

      <div className="flex justify-end">
        <Button onClick={onClose} size="large">
          Close
        </Button>
      </div>
    </Modal>
  );
}
