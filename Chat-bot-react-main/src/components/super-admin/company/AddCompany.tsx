import { Button, Modal } from "antd";
import { useAddCompany } from "../../../hooks/useAddCompany";
import AppInput from "../../../share/form/AppInput";
import AppSelect from "../../../share/form/AppSelect";
import useSWR from "swr";
import AppPassword from "../../../share/form/AppPassword";
interface AddCompanyProps{
    isModalOpen:boolean,
    onCancel:()=>void,
    loading:boolean,
    setLoading:(arg:boolean)=>void,
    mutate:()=>void;
    companyId:number | null;
}
export default function AddCompany({isModalOpen,onCancel,setLoading,loading,mutate,companyId}:AddCompanyProps) {
    const handleCloseModal=()=>{
        onCancel()
        reset()
    }

     const {data}=useSWR('/auth/list-plans/')
 
     const planList=data?.map((item:{id:number,plan_name_display:string})=>({label:item?.plan_name_display,value:item?.id}))

    const{formSubmit,formHooks}=useAddCompany({setLoading,handleCloseModal,mutate,companyId})
    const {control,reset}=formHooks;
  
  return (
     <Modal width={700} className=""  title={companyId?"Edit Company":"Add Company"} footer={()=>(
          <div className="flex gap-2 items-center justify-end">
            <Button type="text" onClick={handleCloseModal}>Cancel</Button>
            <Button type="primary" htmlType="submit"  form="add-company" loading={loading}>Save</Button>
          </div>
        )} open={isModalOpen} onCancel={handleCloseModal} centered>
            <form onSubmit={formSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-3" id="add-company">
          <AppInput control={control} name="name" label="Name" placeholder="Enter name"/>
           <AppInput control={control} name="email" label="Email" placeholder="Enter email" />
          <AppInput control={control} name="address" label="Address" placeholder="Enter address"/>
          <AppInput control={control} name="contact_person" label="Contact Person" placeholder="Enter contact person"/>
          <AppInput control={control} name="contact_number" label="Contact number" placeholder="Enter contact number"/>
          <AppInput control={control} name="phone_number" label="Phone Number" placeholder="Enter phone number"/>
         <AppSelect control={control} name="plan_id" label="Plan" placeholder="Select Plan" options={planList}/>
         {companyId && <AppPassword control={control} name="generated_password" label="Generated Password" placeholder="Enter password"/>}
            </form>
        </Modal>
  )
}
