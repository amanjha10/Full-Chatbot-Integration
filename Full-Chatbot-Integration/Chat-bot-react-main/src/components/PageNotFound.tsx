import { Button, Result } from "antd";
import { useNavigate } from "react-router-dom";


export default function PageNotFound() {
    const navigate=useNavigate()
  return (
     <Result
    status="404"
    title="404"
    subTitle="Sorry, the page you visited does not exist."
    extra={<Button type="primary" className="!bg-yellow" onClick={()=>navigate(-1)}>Back Home</Button>}
  />

  )
}
