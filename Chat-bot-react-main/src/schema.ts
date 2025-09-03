import z from "zod";
export const schemaOfAddUser = z.object({
  name: z.string().min(1, "Please enter the name"),
  phone: z.coerce.number().min(10, "Phone number must be at least 10 digit"),
  email: z.string().min(1, "Please enter the email").email("Invalid email"),
  password: z.string().min(8, "Password must be 8 character"),
  specialization: z.string().min(1, "Please select the specialization"),
});
export const schemaOfAgent = z.object({
  name: z.string().min(1, "Please enter the name"),
  phone: z
    .string()
    .min(10, "Phone number must be at least 10 digits")
    .max(10, "Phone number must be at most 10 digits")
    .regex(/^\d+$/, "Phone number must contain only digits"),
  email: z.string().min(1, "Please enter the email").email("Invalid email"),
  specialization: z.string().min(1, "Please enter the specialization"),
});

export const schemaOfLogin = z.object({
  email: z.string().min(1, "Please enter the email"),
  password: z.string().min(1, "Please enter the password"),
  // First login fields (optional)
  current_password: z.string().optional(),
  new_password: z.string().optional(),
  confirm_password: z.string().optional(),
});

export const schemaOfAddPlan = z.object({
  plan_name: z
    .string()
    .min(1, "Please enter the name")
    .nonempty("Please enter the name"),
  max_agents: z.coerce.number().min(1, "Please enter the user"),
  price: z.coerce.number().min(1, "Please enter the price"),
  company_name: z.string().min(1, "Please enter the company name"),
  expiry_date: z.string().min(1, "Please enter the expiry date"),
});

export const schemaOfAddCompany = z.object({
  name: z.string().min(1, "Please enter the name"),
  contact_person: z.string().min(1, "Please enter the contact person"),
  email: z.string().email("Invalid email"),
  address: z.string().min(1, "Please enter the address"),
  contact_number: z
    .string()
    .regex(/^[0-9]{10}$/, "Phone number must be exactly 10 digits"),
  phone_number: z
    .string()
    .regex(/^[0-9]{10}$/, "Phone number must be exactly 10 digits"),
  plan_id: z.string().min(1, "Please select a plan type"),
  expiry_date: z.string().min(1, "Please select expiry date"),
  custom_max_agents: z.coerce.number().optional(),
  custom_price: z.coerce.number().optional(),
  generated_password: z.string().optional(),
});
