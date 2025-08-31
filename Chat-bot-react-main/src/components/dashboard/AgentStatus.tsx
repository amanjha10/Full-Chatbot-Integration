import { Button, Tag } from "antd";
import { FaUsers } from "react-icons/fa6";
import { HiRefresh } from "react-icons/hi";

export default function AgentStatus() {
  return (
    <div className="p-4 bg-white rounded-md space-y-5 mb-4">
        <div className="flex items-center justify-between">
 <div className="flex items-center gap-3">
            <FaUsers size={20} />
            <p className="text-lg font-bold ">Agent Status</p>
        </div>
        <Button icon={<HiRefresh />
} size="small" type="primary" className="!bg-yellow">Refresh</Button>
        </div>
        <div className="w-full bg-gray-100 rounded-xl p-7 border border-gray-300 space-y-3">
            <div className="flex items-center justify-between">
 <h3 className="text-lg font-semibold">Krishna</h3>
 <Tag className="!bg-yellow-500 ">Busy</Tag>
            </div>        
<div className="flex justify-between">
    <div className="space-y-1">
     <h2 className="text-xl font-bold">10</h2>
     <p className="text-base font-normal">Active</p>
    </div>
     <div className="space-y-1">
     <h2 className="text-xl font-bold">20</h2>
     <p className="text-base font-normal">Capacity</p>
    </div>
     <div className="space-y-1">
     <h2 className="text-xl font-bold">10</h2>
     <p className="text-base font-normal">Load</p>
    </div>
</div>

<p className="font-normal text-base text-gray-500"><span className="text-purple-950 font-medium">Specialization</span>: documentation</p>
        </div>
         <div className="w-full bg-white rounded-xl p-7 border border-gray-300 space-y-3">
            <div className="flex items-center justify-between">
 <h3 className="text-lg font-semibold">Krishna</h3>
 <Tag className="!bg-yellow-500 ">Busy</Tag>
            </div>        
<div className="flex justify-between">
    <div className="space-y-1">
     <h2 className="text-xl font-bold">10</h2>
     <p className="text-base font-normal">Active</p>
    </div>
     <div className="space-y-1">
     <h2 className="text-xl font-bold">20</h2>
     <p className="text-base font-normal">Capacity</p>
    </div>
     <div className="space-y-1">
     <h2 className="text-xl font-bold">10</h2>
     <p className="text-base font-normal">Load</p>
    </div>
</div>

<p className="font-normal text-base text-gray-500"><span className="text-purple-950 font-medium">Specialization</span>: documentation</p>
        </div>
    </div>
  )
}
