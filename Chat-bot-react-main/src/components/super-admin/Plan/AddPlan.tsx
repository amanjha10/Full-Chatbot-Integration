import { Button, Modal } from "antd";
import { useAddPlan } from "../../../hooks/useAddPlan";
import AppInput from "../../../share/form/AppInput";
interface AddPlanProps{
    isModalOpen:boolean,
    onCancel:()=>void,
    setLoading:(arg:boolean)=>void,
    loading:boolean;
    mutate:()=>void
}
export default function AddPlan({isModalOpen,onCancel,setLoading,loading,mutate}:AddPlanProps) {
   const handleCloseModal=()=>{
        onCancel();
        reset({})
    }
    const {formHooks,formSubmit}=useAddPlan({setLoading,handleCloseModal,mutate});
    const {control,reset}=formHooks;
  return (
    <Modal width={400} className=""  title="Add Plan" footer={()=>(
          <div className="flex gap-2 items-center justify-end">
            <Button type="text" onClick={handleCloseModal}>Cancel</Button>
            <Button type="primary" htmlType="submit"  form="add-plan" loading={loading}>Save</Button>
          </div>
        )} open={isModalOpen} onCancel={handleCloseModal} centered>
            <form onSubmit={formSubmit} id="add-plan" className="space-y-3">
          <AppInput control={control} name="plan_name" label="Name" placeholder="Enter name"/>
          <AppInput type="number" control={control} name="max_agents" label="User" placeholder="Enter User "/>
          <AppInput type="number" control={control} name="price" label="Price" placeholder="Enter price"/>
            </form>
        </Modal>
  )
}
