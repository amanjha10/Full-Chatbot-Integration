import { Button, Modal } from "antd";
import { useAddCompany } from "../../../hooks/useAddCompany";
import AppInput from "../../../share/form/AppInput";
import AppSelect from "../../../share/form/AppSelect";
import useSWR from "swr";
import AppPassword from "../../../share/form/AppPassword";

interface AddCompanyProps {
  isModalOpen: boolean;
  onCancel: () => void;
  loading: boolean;
  setLoading: (arg: boolean) => void;
  mutate: () => void;
  companyId: number | null;
}

export default function AddCompany({
  isModalOpen,
  onCancel,
  setLoading,
  loading,
  mutate,
  companyId,
}: AddCompanyProps) {
  const handleCloseModal = () => {
    onCancel();
    reset();
  };

  // Get plan types for dropdown (Bronze, Silver, Gold, Platinum, Diamond, Custom)
  const { data: planTypesData } = useSWR("/auth/plan-types/");

  const planTypeOptions =
    planTypesData?.map(
      (item: { value: string; label: string; is_custom: boolean }) => ({
        label: item.label,
        value: item.value,
      })
    ) || [];

  const { formSubmit, formHooks } = useAddCompany({
    setLoading,
    handleCloseModal,
    mutate,
    companyId,
  });
  const { control, reset, watch } = formHooks;

  // Watch for plan selection to show custom fields
  const selectedPlan = watch("plan_id");
  const isCustomPlan = selectedPlan === "custom";

  return (
    <Modal
      width={700}
      className=""
      title={companyId ? "Edit Company" : "Add Company"}
      footer={() => (
        <div className="flex gap-2 items-center justify-end">
          <Button type="text" onClick={handleCloseModal}>
            Cancel
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            form="add-company"
            loading={loading}
          >
            Save
          </Button>
        </div>
      )}
      open={isModalOpen}
      onCancel={handleCloseModal}
      centered
    >
      <form
        onSubmit={formSubmit}
        className="grid grid-cols-1 md:grid-cols-2 gap-3"
        id="add-company"
      >
        <AppInput
          control={control}
          name="name"
          label="Name"
          placeholder="Enter name"
        />
        <AppInput
          control={control}
          name="email"
          label="Email"
          placeholder="Enter email"
        />
        <AppInput
          control={control}
          name="address"
          label="Address"
          placeholder="Enter address"
        />
        <AppInput
          control={control}
          name="contact_person"
          label="Contact Person"
          placeholder="Enter contact person"
        />
        <AppInput
          control={control}
          name="contact_number"
          label="Contact number"
          placeholder="Enter contact number"
        />
        <AppInput
          control={control}
          name="phone_number"
          label="Phone Number"
          placeholder="Enter phone number"
        />
        <AppSelect
          control={control}
          name="plan_id"
          label="Plan"
          placeholder="Select Plan"
          options={planTypeOptions}
        />
        <AppInput
          control={control}
          name="expiry_date"
          label="Expiry Date"
          placeholder="YYYY-MM-DD"
          type="date"
        />

        {/* Show custom fields when Custom plan is selected */}
        {isCustomPlan && (
          <>
            <AppInput
              control={control}
              name="custom_max_agents"
              label="Max Agents"
              placeholder="Enter max agents"
              type="number"
            />
            <AppInput
              control={control}
              name="custom_price"
              label="Price"
              placeholder="Enter price"
              type="number"
            />
          </>
        )}

        {companyId && (
          <AppPassword
            control={control}
            name="generated_password"
            label="Generated Password"
            placeholder="Enter password"
          />
        )}
      </form>
    </Modal>
  );
}
