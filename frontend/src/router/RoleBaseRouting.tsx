import { Navigate } from "react-router-dom"
import { useAuth } from "../store/AuthStore"
interface RoleBaseRoutingProps{
    roles:string,
    children:React.ReactNode
}
export default function RoleBaseRouting({roles,children}:RoleBaseRoutingProps) {
    const context=useAuth()
    console.log("role",context?.role)
  return context?.role==roles ? (<div>{children}</div>):<Navigate to="/login" replace/>
}
