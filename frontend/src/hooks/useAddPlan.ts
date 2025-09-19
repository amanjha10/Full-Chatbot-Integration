import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { schemaOfAddPlan } from "../schema";
import z from "zod";
import { createPlan } from "../api/post";
import { useMessageContext } from "../context-provider/MessageProvider";
type FormType = z.infer<typeof schemaOfAddPlan>;
interface AddPlanProps {
  setLoading: (arg: boolean) => void;
  handleCloseModal: () => void;
  mutate: () => void;
}
export const useAddPlan = ({
  setLoading,
  handleCloseModal,
  mutate,
}: AddPlanProps) => {
  const { messageApi } = useMessageContext();
  const formHooks = useForm({
    resolver: zodResolver(schemaOfAddPlan),
    mode: "onChange",
    defaultValues: {
      plan_name: "",
      max_agents: undefined,
      price: undefined,
      company_name: "",
      expiry_date: "",
    },
  });
  const { handleSubmit } = formHooks;
  const onSubmit = (data: FormType) => {
    setLoading(true);
    createPlan(data)
      .then(() => {
        setLoading(false);
        handleCloseModal();
        messageApi.success("Plan Create Successfully");
        mutate();
      })
      .catch((err) => {
        setLoading(false);
        messageApi.error(err?.response?.data?.plan_name?.[0]);
      });
  };
  return { formHooks, formSubmit: handleSubmit(onSubmit) };
};
