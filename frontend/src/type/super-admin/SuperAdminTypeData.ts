type SuperAdmin = {
  name: string;
  email: string;
  address: string;
  contact_person: string;
  contact_number: string;
  phone_number: string;
  plan: number;
  plan_id: number | string;
  id: number;
  generated_password: string;
  plan_name: string;
  max_agents: number;
  price: number;
  company_name: string;
  expiry_date: string;
  custom_max_agents?: number;
  custom_price?: number;
};

export type CompanyPayloadType = Pick<
  SuperAdmin,
  | "address"
  | "contact_number"
  | "contact_person"
  | "email"
  | "name"
  | "phone_number"
  | "plan_id"
  | "expiry_date"
  | "custom_max_agents"
  | "custom_price"
>;
export type CompanyListType = Pick<
  SuperAdmin,
  | "address"
  | "contact_number"
  | "contact_person"
  | "email"
  | "name"
  | "phone_number"
>;
export type PlanPayloadType = Pick<
  SuperAdmin,
  "plan_name" | "max_agents" | "price" | "company_name" | "expiry_date"
>;
