import { Button, Modal } from "antd";
import { useAddUser } from "../../hooks/useAddUser";
import AppInput from "../../share/form/AppInput";
import AppPassword from "../../share/form/AppPassword";
import AppSelect from "../../share/form/AppSelect";
interface AddUserProps{
    isModalOpen:boolean,
    onCancel:()=>void
}
export default function AddUserModal({isModalOpen,onCancel}:AddUserProps) {
 const {formHooks,formSubmit}=useAddUser();
 const {control,reset}=formHooks;
 const handleCloseModal=()=>{
  onCancel();
  reset({})
 }
  return (
    <div>
        <Modal width={700} className=""  title="Add User" footer={()=>(
          <div className="flex gap-2 items-center justify-end">
            <Button type="text" onClick={handleCloseModal}>Cancel</Button>
            <Button type="primary" htmlType="submit"  form="add-user">Add</Button>
          </div>
        )} open={isModalOpen} onCancel={handleCloseModal} centered>
         <form onSubmit={formSubmit} className="space-y-4 grid grid-cols-2 gap-3" id="add-user">
         <AppInput control={control} name="name" label="Name" placeholder="Enter name"/>
         <AppInput control={control} type="number"   name="phone" label="Phone" placeholder="Enter phone number"/>
         <AppInput control={control} name="email" label="Email" placeholder="Enter email"/>
         <AppPassword control={control} name="password" label="Password" placeholder="Enter password"/>
         <AppSelect control={control} name="specialization" label="specialization" placeholder="Select specialization" options={[]}/>
         </form>
          </Modal>
    </div>
  )
}
