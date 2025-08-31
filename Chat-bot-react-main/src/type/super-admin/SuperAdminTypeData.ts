type SuperAdmin={
    name:string;
    email:string;
    address:string;
    contact_person:string,
    contact_number:string,
    phone_number:string,
    plan:number,
    plan_id:number,
    id:number,
    generated_password:string
    plan_name:string
    max_agents:number
    price:number
}

export type CompanyPayloadType=Pick<SuperAdmin,'address'|'contact_number'|'contact_person'|'email'|'name'|'phone_number'|'plan_id'>
export type CompanyListType=Pick<SuperAdmin,'address'|'contact_number'|'contact_person'|'email'|'name'|'phone_number'>
export type PlanPayloadType=Pick<SuperAdmin,"plan_name"|'max_agents'|'price' >