import { Button, Modal, Select, Form, Input } from "antd";
import { FiPlus } from "react-icons/fi";
import AppTable from "../../share/form/AppTable";
import { useCoumnsCompany } from "../../TableColumns/useColumnsCompany";
import { useState } from "react";
import AddCompany from "../../components/super-admin/company/AddCompany";
import AppDeleteModal from "../../components/AppDeleteModal";
import useSWR from "swr";
import type { CompanyListType } from "../../type/super-admin/SuperAdminTypeData";
import { useMessageContext } from "../../context-provider/MessageProvider";
import { deleteCompany } from "../../api/delete";
import { useSearchParams } from "react-router-dom";
import { axiosClient } from "../../config/axiosConfig";
import { getPlanTypes } from "../../api/get";

export default function Company() {
  const { messageApi } = useMessageContext();
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isDeleteOpenModal, setIsDeleteModal] = useState<boolean>(false);
  const [isCancelSubscriptionModal, setIsCancelSubscriptionModal] = useState<boolean>(false);
  const [isReactivateSubscriptionModal, setIsReactivateSubscriptionModal] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [name, setName] = useState<string>("");
  const [searchParams, setSearchParams] = useSearchParams({});
  const page = Number(searchParams.get("page")) || 1;
  const [form] = Form.useForm();
  const handleCloseModal = () => {
    console.log("Closing modal");
    setIsModalOpen(false);
    setCompanyId(null);
  };

  const handleCloseDeleteModal = () => {
    setIsDeleteModal(false);
    setName("");
    setCompanyId(null);
  };

  const handleDeleteOpenModal = (companyName: string, id: number) => {
    setIsDeleteModal(true);
    setName(companyName);
    setCompanyId(id);
  };

  const handleCancelSubscriptionModal = (companyName: string, id: number) => {
    setIsCancelSubscriptionModal(true);
    setName(companyName);
    setCompanyId(id);
  };

  const handleReactivateSubscriptionModal = (companyName: string, id: number) => {
    setIsReactivateSubscriptionModal(true);
    setName(companyName);
    setCompanyId(id);
  };

  const handleDeleteCompany = () => {
    setLoading(true);
    deleteCompany(companyId)
      .then(() => {
        messageApi.success("Delete Company Successfully");
        handleCloseDeleteModal();
        mutate();
        setLoading(false);
      })
      .catch((err) => {
        messageApi.error(err?.message);
        setLoading(false);
      });
  };

  const handleCancelSubscription = async () => {
    if (!companyId) return;

    setLoading(true);
    try {
      const reason = form.getFieldValue('reason') || 'Subscription cancelled by admin';

      await axiosClient.post(`/auth/cancel-subscription/${companyId}/`, {
        reason: reason
      });

      messageApi.success("Subscription cancelled successfully");
      setIsCancelSubscriptionModal(false);
      setName("");
      setCompanyId(null);
      form.resetFields();
      mutate();
    } catch (error: any) {
      messageApi.error(error?.response?.data?.error || "Failed to cancel subscription");
    } finally {
      setLoading(false);
    }
  };

  const handleReactivateSubscription = async () => {
    if (!companyId) return;

    setLoading(true);
    try {
      const planId = form.getFieldValue('plan_id');
      const reason = form.getFieldValue('reason') || 'Subscription reactivated by admin';

      if (!planId) {
        messageApi.error("Please select a plan");
        setLoading(false);
        return;
      }

      await axiosClient.post(`/auth/reactivate-subscription/${companyId}/`, {
        plan_id: planId,
        reason: reason
      });

      messageApi.success("Subscription reactivated successfully");
      setIsReactivateSubscriptionModal(false);
      setName("");
      setCompanyId(null);
      form.resetFields();
      mutate();
    } catch (error: any) {
      messageApi.error(error?.response?.data?.error || "Failed to reactivate subscription");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenAddCompanyModal = () => {
    console.log("Add Company button clicked");
    setIsModalOpen(true);
    setCompanyId(null); // For adding new company
    console.log("Modal state set to true, companyId set to null");
  };

  const handleOpenViewCompanyModal = (id: number) => {
    setIsModalOpen(true);
    setCompanyId(id);
  };

  const handlePagination = (pagination: number) => {
    setSearchParams({
      page: pagination.toString(),
    });
  };

  const handleResetPassword = async (adminId: number, email: string) => {
    try {
      const response = await axiosClient.post("/auth/reset-admin-password/", {
        admin_id: adminId,
      });

      const { new_password } = response.data;
      messageApi.success(
        `Password reset successfully!
        Email: ${email}
        New Password: ${new_password}
        Admin must use this password for first login.`
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
  };

  const { columns } = useCoumnsCompany({
    handleOpenViewCompanyModal,
    handleDeleteOpenModal,
    handleCancelSubscription: handleCancelSubscriptionModal,
    handleReactivateSubscription: handleReactivateSubscriptionModal,
    handleResetPassword,
  });
  const { data, isLoading, mutate } = useSWR(`/auth/list-admins/?page=${page}`);
  const { data: planTypesResponse, error: planTypesError } = useSWR('/auth/plan-types/', getPlanTypes);

  // Safely extract planTypes data
  const planTypes = planTypesResponse?.data || [];

  // Debug planTypes data (remove in production)
  if (planTypesError) {
    console.error('Error loading plan types:', planTypesError);
  }

  // DEAD CODE REMOVED - Debug console.log removed for production

  const tableData = data?.results.map(
    (adminItem: CompanyListType, index: number) => ({
      sn: index + 1,
      ...adminItem,
    })
  );
  const totalCount = data?.count;
  return (
    <div className="pt-4 space-y-5">
      <h2 className="font-bold text-2xl">Company</h2>
      <div className="space-y-4">
        <div className="flex justify-between">
          <h6 className="font-bold text-xl">Company List</h6>
          <Button
            type="primary"
            icon={<FiPlus size={15} />}
            onClick={handleOpenAddCompanyModal}
          >
            Add
          </Button>
        </div>
        <AppTable
          total={totalCount}
          paginationData={page}
          handlePagination={handlePagination}
          columns={columns}
          dataSource={tableData}
          loading={isLoading}
          rowKey="id"
        />
        {isModalOpen && (
          <AddCompany
            companyId={companyId}
            mutate={mutate}
            isModalOpen={isModalOpen}
            onCancel={handleCloseModal}
            loading={loading}
            setLoading={setLoading}
          />
        )}
        {isDeleteOpenModal && (
          <AppDeleteModal
            loading={loading}
            name={name}
            isDeleteOpenModal={isDeleteOpenModal}
            handleCancel={handleCloseDeleteModal}
            onDelete={handleDeleteCompany}
          />
        )}

        {/* Cancel Subscription Modal */}
        <Modal
          title="Cancel Subscription"
          open={isCancelSubscriptionModal}
          onOk={handleCancelSubscription}
          onCancel={() => {
            setIsCancelSubscriptionModal(false);
            setName("");
            setCompanyId(null);
            form.resetFields();
          }}
          confirmLoading={loading}
          okText="Cancel Subscription"
          okButtonProps={{ danger: true }}
        >
          <Form form={form} layout="vertical">
            <p>Are you sure you want to cancel the subscription for <strong>{name}</strong>?</p>
            <p className="text-sm text-gray-600 mb-4">
              This will disable the chatbot widget but preserve all company data.
              The subscription can be reactivated later.
            </p>
            <Form.Item
              name="reason"
              label="Reason for cancellation (optional)"
            >
              <Input.TextArea
                rows={3}
                placeholder="Enter reason for cancelling subscription..."
              />
            </Form.Item>
          </Form>
        </Modal>

        {/* Reactivate Subscription Modal */}
        <Modal
          title="Reactivate Subscription"
          open={isReactivateSubscriptionModal}
          onOk={handleReactivateSubscription}
          onCancel={() => {
            setIsReactivateSubscriptionModal(false);
            setName("");
            setCompanyId(null);
            form.resetFields();
          }}
          confirmLoading={loading}
          okText="Reactivate Subscription"
        >
          <Form form={form} layout="vertical">
            <p>Reactivate subscription for <strong>{name}</strong></p>
            <p className="text-sm text-gray-600 mb-4">
              Select a plan to reactivate the subscription and enable the chatbot widget.
            </p>
            <Form.Item
              name="plan_id"
              label="Select Plan"
              rules={[{ required: true, message: 'Please select a plan' }]}
            >
              <Select placeholder="Choose a plan">
                {Array.isArray(planTypes) && planTypes.map((plan: any) => (
                  <Select.Option key={plan.value} value={plan.value}>
                    {plan.label}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item
              name="reason"
              label="Reason for reactivation (optional)"
            >
              <Input.TextArea
                rows={3}
                placeholder="Enter reason for reactivating subscription..."
              />
            </Form.Item>
          </Form>
        </Modal>
      </div>
    </div>
  );
}
