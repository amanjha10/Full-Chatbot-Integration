
import { useState } from "react";
import PlanCard from "../../components/super-admin/Plan/PlanCard";
import AddPlan from "../../components/super-admin/Plan/AddPlan";
import { Button } from "antd";
import { FiPlus } from "react-icons/fi";
import useSWR from "swr";

export default function Plan() {
    const[isModalOpen,setIsModalOpen]=useState<boolean>(false);
    const[loading,setLoading]=useState<boolean>(false);
    const handleCloseModal=()=>{
        setIsModalOpen(false)
    }
    const {data,isLoading,mutate}=useSWR('/auth/list-plans/')
    if(isLoading) return <h3>Loading...</h3>
  return (
    <div className="pt-4 space-y-5">
          <h2 className="font-bold text-2xl">Plan</h2>
          <div className="space-y-4">
            <div className="flex justify-end">
                <Button type="primary" icon={<FiPlus size={15} />} onClick={()=>setIsModalOpen(true)} >Add</Button>
            </div>
            <div className="grid grid-col-2 md:grid-cols-2  xl:grid-cols-4 gap-6">
              {data?.map((planItem:any)=>(
                <div key={planItem?.id}>
                      <PlanCard planName={planItem?.plan_name} max_agents={planItem?.max_agents} price={planItem?.price}/>
                </div>
              ))}
            </div>
          </div>
          {isModalOpen && <AddPlan mutate={mutate} isModalOpen={isModalOpen} onCancel={handleCloseModal} setLoading={setLoading} loading={loading}/>}
    </div>
  )
}
