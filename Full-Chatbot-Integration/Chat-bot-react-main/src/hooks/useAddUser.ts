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
    console.log("data",data)
}
return {formHooks,formSubmit:handleSubmit(onSubmit)}
}