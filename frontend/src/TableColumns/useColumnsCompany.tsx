import { Dropdown, type MenuProps } from "antd"
import type { ColumnsType } from "antd/es/table"
import { BsThreeDotsVertical } from "react-icons/bs"
import { IoEyeOutline } from "react-icons/io5"
import { MdDeleteOutline, MdCancel } from "react-icons/md"
import { RiResetLeftFill } from "react-icons/ri"
import { FiPlay } from "react-icons/fi"

interface useColumnsCompanyProps{
    handleOpenViewCompanyModal:(id:number)=>void;
    handleDeleteOpenModal:(companyName:string,id:number)=>void;
    handleCancelSubscription:(companyName:string,id:number)=>void;
    handleReactivateSubscription:(companyName:string,id:number)=>void;
    handleResetPassword:(id:number,email:string)=>void;
}

export const useCoumnsCompany=({handleOpenViewCompanyModal,handleDeleteOpenModal,handleCancelSubscription,handleReactivateSubscription,handleResetPassword}:useColumnsCompanyProps)=>{
 const getItemMenu=(row:any):MenuProps['items']=>[
  {
       label: "View",
       key: "1",
       icon:<IoEyeOutline size={17} />,
       onClick:()=>{
        handleOpenViewCompanyModal(row?.id)
       }
     },
     {
       label: "Reset Password",
       key: "2",
       icon:<RiResetLeftFill size={17} />,
       onClick:()=>{
        handleResetPassword(row?.id, row?.email)
       }
     },

     {
       label: "Delete Company",
       key: "3",
       icon:<MdDeleteOutline size={17} />,
       danger: true,
       onClick:()=>{
       handleDeleteOpenModal(row?.name,row?.id)
       }
     },
 ]
    const columns:ColumnsType=[
        {
            title:'Sn',
            render:({sn})=><p>{sn}</p>
        },
        {
            title:"Name",
            render:({name})=><p>{name}</p>
        },
        {
            title:'Contact Person',
            render:({contact_person})=><p>{contact_person}</p>
        },
        {
            title:"Contact Number",
            render:({contact_number})=><p>{contact_number}</p>
        },
        {
            title:"Phone Number",
            render:({phone_number})=><p>{phone_number}</p>
        },
        {
            title:"email",
            render:({email})=><p>{email}</p>
        },
        {
            title:"Address",
            render:({address})=><p>{address}</p>
        },
        {   
            align:"right",
            title:"Action",
            width:100,
            render:(row)=>{
                return(
                    <div className="float-right">
                        <Dropdown menu={{ items: getItemMenu(row) }}trigger={["click"]}>
<BsThreeDotsVertical className="cursor-pointer"/>
                        </Dropdown>

                    </div>
                    
                )
            }
        }
    ]
    return {columns}
}