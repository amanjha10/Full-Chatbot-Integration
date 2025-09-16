import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form"
import { schemaOfAddUser } from "../schema";
import type z from "zod";
type FormType=z.infer<typeof schemaOfAddUser>
export const useAddUser=()=>{
const formHooks=useForm({
    resolver:zodResolver(schemaOfAddUser),
    mode:"onChange",
    defaultValues:{
        name:"",
        phone:undefined,
        email:"",
        password:"",
        specialization:""
    }
});
const {handleSubmit}=formHooks;
const onSubmit=(data:FormType)=>{
    // DEAD CODE REMOVED - Debug console.log removed
    // TODO: Implement actual user creation logic
}
return {formHooks,formSubmit:handleSubmit(onSubmit)}
}