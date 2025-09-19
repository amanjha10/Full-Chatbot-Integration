
import { Input } from "antd"
import { Controller, type Control, type FieldValues, type Path } from "react-hook-form"
interface AppPasswordProps<T extends FieldValues>{
    name:Path<T>,
    control:Control<T>
    placeholder:string,
    label?:string,
}
export default function AppPassword<T extends FieldValues>({name,control,placeholder,label,...rest}:AppPasswordProps<T>) {
  return (
     <div className="space-y-2 w-full">
    <p className="text-sm font-normal text-gray-700">{label}</p>
    <Controller
    name={name}
    control={control}
    render={({field:{value,onChange},fieldState:{error}})=>(
 <div className="space-y-1">
        <Input.Password status={error && "error"} value={value} onChange={onChange
          }
         className="w-full"  placeholder={placeholder}  {...rest}/>
         {error && ( <p className="text-xs text-red-500 font-normal">{error?.message}</p>)}
        </div>
    )}
    />
    </div>
  )
}
