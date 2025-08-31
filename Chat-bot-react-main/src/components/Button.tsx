import { Button } from "antd"
interface ButtonProps{
    type?:"link" | "text" | "default" | "primary" | "dashed" | undefined
    children:React.ReactNode,
    className?:string
    onClick?:React.MouseEventHandler<HTMLButtonElement>
    htmlType?:"submit" | "button" | "reset" | undefined
    form?:string
    loading?:boolean
    danger?:boolean
    icons?:React.ReactElement
}

export default function PrimaryButton({type,children,className,onClick ,htmlType,form,loading,danger,icons}:ButtonProps) {
  return (
    <Button icon={icons} iconPosition="end" type={type} danger={danger} className={className} onClick={onClick} htmlType={htmlType} form={form} loading={loading}>{children}</Button>
  )
}
