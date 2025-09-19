import { Button } from "antd";
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
        {/* DUPLICATE CODE REMOVED - Hardcoded agent data replaced with placeholder */}
        <div className="w-full bg-gray-100 rounded-xl p-7 border border-gray-300 space-y-3">
            <div className="flex items-center justify-center py-8">
                <p className="text-gray-500 text-center">
                    Agent status will be displayed here when connected to real data.
                    <br />
                    <span className="text-sm">TODO: Connect to agent status API</span>
                </p>
            </div>
        </div>
    </div>
  )
}
