import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { schemaOfAddCompany } from "../schema";
import type z from "zod";
import { createCompany } from "../api/post";
import { useMessageContext } from "../context-provider/MessageProvider";
import useSWR from "swr";
import { useEffect } from "react";
import { editCompany } from "../api/Put";

type FormType = z.infer<typeof schemaOfAddCompany>;

interface AddCompanyProps {
  setLoading: (arg: boolean) => void;
  handleCloseModal: () => void;
  mutate: () => void;
  companyId: number | null;
}

export const useAddCompany = ({
  setLoading,
  handleCloseModal,
  mutate,
  companyId,
}: AddCompanyProps) => {
  const { data } = useSWR(
    companyId ? `/auth/list-admins/?admin_id=${companyId}` : ""
  );
  const { messageApi } = useMessageContext();
  const formHooks = useForm({
    resolver: zodResolver(schemaOfAddCompany),
    mode: "onChange",
    defaultValues: {
      name: "",
      contact_person: "",
      email: "",
      address: "",
      contact_number: "",
      phone_number: "",
      plan_id: "",
      expiry_date: "",
      custom_max_agents: undefined,
      custom_price: undefined,
    },
  });
  const { handleSubmit, reset } = formHooks;
  const onSubmit = (data: FormType) => {
    setLoading(true);
    if (companyId) {
      editCompany(data, companyId)
        .then(() => {
          messageApi.success("Update Company Successfully");
          setLoading(false);
          handleCloseModal();
          mutate();
        })
        .catch((err) => {
          messageApi.error(err?.message);
          setLoading(false);
        });
    } else {
      createCompany(data)
        .then(() => {
          messageApi.success("Company Create Successfully");
          setLoading(false);
          handleCloseModal();
          mutate();
        })
        .catch((err) => {
          messageApi.error(err?.message);
          setLoading(false);
        });
    }
  };
  useEffect(() => {
    reset({
      ...data,
      plan_id: data?.current_plan?.plan_id,
    });
  }, [companyId, data, reset]);
  return { formHooks, formSubmit: handleSubmit(onSubmit) };
};
