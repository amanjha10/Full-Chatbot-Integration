import { DeleteOutlined } from "@ant-design/icons";
import { Button, Modal } from "antd";

interface DeleteModalProps {
  name?:string
  loading?: boolean
  isDeleteOpenModal: boolean,
  handleCancel: () => void
  onDelete: () => void
}


export default function AppDeleteModal({name, loading, isDeleteOpenModal, handleCancel, onDelete }: DeleteModalProps) {
  return (
    <Modal
      centered
      open={isDeleteOpenModal}
      onCancel={handleCancel}
      footer={() => (
        <div className="flex item-center gap-2 justify-end">
          <Button type="default" onClick={handleCancel}>Cancel</Button>
          <Button type="primary" danger onClick={onDelete} loading={loading}>Delete</Button>
        </div>

      )}
    >
      <div className="flex gap-3">
        <DeleteOutlined  className="text-4xl " style={{color:"red"}} />
        <div>
          <h2 className="text-xl font-semibold text-red-500">Delete</h2>
          <p className="text-sm  text-red-500">{`Are you sure want to  delete ${name}?`}</p>
        </div>
      </div>
    </Modal>

  )
}