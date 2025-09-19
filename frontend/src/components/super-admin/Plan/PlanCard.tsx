import { FaUsers, FaRupeeSign } from "react-icons/fa";
interface PlanCardProps{
  planName:string;
  max_agents:number;
  price:string
}
export default function PlanCard({planName,max_agents,price}:PlanCardProps) {
  return (
    <div className="p-6 bg-white rounded-md shadow-md hover:shadow-xl transition-shadow duration-300 space-y-4 border border-gray-100">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold text-gray-900">{planName}</h3>
        <span className="px-3 py-1 text-sm font-medium bg-yellow text-white rounded-full">
          Popular
        </span>
      </div>
      <div className="flex items-center gap-2 text-gray-700">
        <FaUsers className="w-5 h-5 text-gray-500" />
        <p className="text-lg">{max_agents} Users</p>
      </div>
      <div className="flex items-center gap-2 text-gray-700">
        <FaRupeeSign className="w-5 h-5 " />
        <p className="text-lg font-semibold text-gray-900">{price}/month</p>
      </div>
    </div>
  );
}
