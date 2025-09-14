import { Select } from "antd"
import { Controller, type Control, type FieldValues, type Path } from "react-hook-form"
interface AppSelectProps<T extends FieldValues>{
    name:Path<T>,
    control:Control<T>
    placeholder:string,
    options:{label:string,value:unknown}[],
    label?:string,
    disabled?:boolean,
}
export default function AppSelect<T extends FieldValues>({name,control,placeholder,options,label,disabled,...rest}:AppSelectProps<T>) {
  return (
    <div className="space-y-2 w-full">
       <p className="text-sm font-normal text-gray-700">{label}</p>
       <Controller
       name={name}
       control={control}
       render={({field:{value,onChange},fieldState:{error}})=>(
        <div className="space-y-1">
        <Select status={error && "error"} value={value} onChange={onChange
          }
          options={options} className="w-full"  disabled={disabled} placeholder={placeholder}  {...rest}/>
         {error && ( <p className="text-xs text-red-500 font-normal">{error?.message}</p>)}
        </div>
       )}/>
    </div>
  )
}
