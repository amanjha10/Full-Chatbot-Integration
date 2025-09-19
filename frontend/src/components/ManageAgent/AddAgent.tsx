import { Button, Modal } from 'antd'
import AppInput from '../../share/form/AppInput'
import { useAddAgent } from '../../hooks/UseAddAgent'
interface AddGentProps{
   isModalOpen:boolean ,
  onCancel:()=>void
  setLoading:(arg:boolean)=>void
  loading:boolean
  mutate:()=>void
}
export default function AddAgent({isModalOpen,onCancel,setLoading,loading,mutate}:AddGentProps) {
   const handleCloseModal=()=>{
        onCancel()
        reset({})
    }
    const {formHooks,formSubmit}=useAddAgent({setLoading,handleCloseModal,mutate})
   
    const{control,reset}=formHooks;
  return (
 <div>
        <Modal width={700} className=""  title="Add Agent" footer={()=>(
          <div className="flex gap-2 items-center justify-end">
            <Button type="text" onClick={handleCloseModal}>Cancel</Button>
            <Button type="primary" htmlType="submit"  form="add-user" loading={loading}>Add</Button>
          </div>
        )} open={isModalOpen} onCancel={handleCloseModal} centered>
         <form onSubmit={formSubmit} className="space-y-4 grid grid-cols-2 gap-3" id="add-user">
         <AppInput control={control} name="name" label="Name" placeholder="Enter name"/>
         <AppInput control={control}   name="phone" label="Phone" placeholder="Enter phone number"/>
         <AppInput control={control} name="email" label="Email" placeholder="Enter email"/>
         <AppInput control={control} name="specialization" label='Specialization' placeholder='Enter specialization'/>
         </form>
          </Modal>
    </div>
  )
}
