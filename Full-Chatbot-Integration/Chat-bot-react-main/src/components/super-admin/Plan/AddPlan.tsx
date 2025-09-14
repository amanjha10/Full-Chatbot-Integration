import { Button, Modal } from "antd";
import { useAddPlan } from "../../../hooks/useAddPlan";
import AppInput from "../../../share/form/AppInput";
import AppSelect from "../../../share/form/AppSelect";

interface AddPlanProps {
  isModalOpen: boolean;
  onCancel: () => void;
  setLoading: (arg: boolean) => void;
  loading: boolean;
  mutate: () => void;
}

export default function AddPlan({
  isModalOpen,
  onCancel,
  setLoading,
  loading,
  mutate,
}: AddPlanProps) {
  const handleCloseModal = () => {
    onCancel();
    reset({});
  };

  const planOptions = [
    { label: "Basic", value: "basic" },
    { label: "Pro", value: "pro" },
    { label: "Premium", value: "premium" },
  ];

  const { formHooks, formSubmit } = useAddPlan({
    setLoading,
    handleCloseModal,
    mutate,
  });
  const { control, reset } = formHooks;
  return (
    <Modal
      width={400}
      className=""
      title="Add Plan"
      footer={() => (
        <div className="flex gap-2 items-center justify-end">
          <Button type="text" onClick={handleCloseModal}>
            Cancel
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            form="add-plan"
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
      <form onSubmit={formSubmit} id="add-plan" className="space-y-3">
        <AppSelect
          control={control}
          name="plan_name"
          label="Plan"
          placeholder="Select plan"
          options={planOptions}
        />
        <AppInput
          type="number"
          control={control}
          name="price"
          label="Plan Price"
          placeholder="Enter plan price"
        />
        <AppInput
          type="number"
          control={control}
          name="max_agents"
          label="Max Agent"
          placeholder="Enter max agent"
        />
        <AppInput
          control={control}
          name="company_name"
          label="Company Name"
          placeholder="Enter company name"
        />
        <AppInput
          type="date"
          control={control}
          name="expiry_date"
          label="Expiry Date"
          placeholder="MM/DD/YYYY"
        />
      </form>
    </Modal>
  );
}
