import { Dropdown, Tag, type MenuProps } from "antd"
import type { ColumnsType } from "antd/es/table"
import { BsThreeDotsVertical } from "react-icons/bs"
import type { AgentListType } from "../type/admin/AdminDataType";
interface useColumnsProps{
    getTagColor:(arg:string)=>string,
    getItemMenu:(row:AgentListType)=> MenuProps["items"]; 
}
export const useColumnsAgentList=({getItemMenu,getTagColor}:useColumnsProps)=>{
    const columns:ColumnsType=[
    {
        title:"SN",
        render:({sn})=><p>{sn}</p>
    },
    {
        title:"Name",
        render:({name})=><p>{name}</p>
    },
    {
        title:"Email",
        render:({email})=><p>{email}</p>
    },
    {
        title:"Phone",
        render:({phone})=><p>{phone}</p>
    },
    {
title:"Specialization",
render:({specialization})=><p>{specialization}</p>
    },
    {
        title:"status",
        render:({status})=><Tag color={getTagColor(status)}>{status}</Tag>
    },
    {
        title:"Last Active",
        render:({formatted_last_active})=><p>{formatted_last_active}</p>
    },
    {  
        width:100,
        title:"Action",
        render:(row)=>{
            return(
                <div>
                    <Dropdown  menu={{ items: getItemMenu(row) }}trigger={["click"]}>
       <BsThreeDotsVertical className="cursor-pointer"/>
                    </Dropdown>
                    
                </div>
            )
        }
    }
]
return {columns}
}