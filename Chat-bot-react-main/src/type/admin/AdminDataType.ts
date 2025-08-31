type AdminDataType={
    agent_id:number
    id:number
    name:string
    email:string
    specialization:string
    company_id:string
    status:string
    formatted_last_active:string
    generated_password:string
    phone:string
}
export type ResetPasswordPayload=Pick<AdminDataType,'agent_id'>
export type AgentListType=Pick<AdminDataType,'company_id'|'email'|'formatted_last_active'|'id'|'generated_password'|'name'|'specialization'|'status'>
export type CreateAgentPayload=Pick<AdminDataType,"name"|'phone'|'specialization'|'email'>