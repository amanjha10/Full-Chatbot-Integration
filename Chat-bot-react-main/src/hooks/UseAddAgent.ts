import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { schemaOfAgent } from "../schema";
import type z from "zod";
import { createAgent } from "../api/post";
import { useMessageContext } from "../context-provider/MessageProvider";
type FormType = z.infer<typeof schemaOfAgent>;
interface AddAgentProps {
  handleCloseModal: () => void;
  setLoading: (args: boolean) => void;
  mutate: () => void;
}
export const useAddAgent = ({
  handleCloseModal,
  setLoading,
  mutate,
}: AddAgentProps) => {
  const { messageApi } = useMessageContext();
  const formHooks = useForm({
    resolver: zodResolver(schemaOfAgent),
    mode: "onChange",
    defaultValues: {
      name: "",
      phone: undefined,
      email: "",
      specialization: "",
    },
  });
  const { handleSubmit } = formHooks;
  const onSubmit = (data: FormType) => {
    setLoading(true);
    createAgent(data)
      .then((response) => {
        const { email, password, agent } = response.data;
        messageApi.success(
          `Agent created successfully!
            Email: ${email}
            Password: ${password}
            Please save these credentials.`
        );
        handleCloseModal();
        setLoading(false);
        mutate();
      })
      .catch((err) => {
        messageApi.error(
          err?.response?.data?.error || err?.message || "Failed to create agent"
        );
        setLoading(false);
      });
  };
  return { formHooks, formSubmit: handleSubmit(onSubmit) };
};
