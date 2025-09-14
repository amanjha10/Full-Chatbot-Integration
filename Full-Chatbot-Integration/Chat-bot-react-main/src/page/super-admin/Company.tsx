import { Button } from "antd";
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

export default function Company() {
  const { messageApi } = useMessageContext();
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [isDeleteOpenModal, setIsDeleteModal] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [name, setName] = useState<string>("");
  const [searchParams, setSearchParams] = useSearchParams({});
  const page = Number(searchParams.get("page")) || 1;
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
    handleResetPassword,
  });
  const { data, isLoading, mutate } = useSWR(`/auth/list-admins/?page=${page}`);

  console.log(
    "Company component render - isModalOpen:",
    isModalOpen,
    "companyId:",
    companyId
  );

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
      </div>
    </div>
  );
}
