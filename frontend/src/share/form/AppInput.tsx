
import { Input } from "antd"
import { Controller, type Control, type FieldValues, type Path } from "react-hook-form"
interface AppInputProps<T extends FieldValues>{
    name:Path<T>,
    control:Control<T>
    placeholder:string,
    label?:string,
    type?:string
}
export default function AppInput<T extends FieldValues>({name,control,placeholder,label,type="text",...rest}:AppInputProps<T>) {
  return (
    <div className="space-y-2 w-full">
    <p className="text-sm font-normal text-gray-700">{label}</p>
    <Controller
    name={name}
    control={control}
    render={({field:{value,onChange},fieldState:{error}})=>(
 <div className="space-y-1">
        <Input type={type} status={error && "error"} value={value} onChange={onChange
          }
         className="w-full"  placeholder={placeholder}  {...rest}/>
         {error && ( <p className="text-xs text-red-500 font-normal">{error?.message}</p>)}
        </div>
    )}
    />
    </div>
  )
}
