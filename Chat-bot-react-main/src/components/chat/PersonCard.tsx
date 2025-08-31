import { Avatar } from "antd";

export default function PersonCard() {
  return (
    <div className="bg-gray-200 rounded-md p-4 flex gap-3 h-[120] w-full cursor-pointer">
        <div className="w-[30px] h-[30px]">
<Avatar size={35} src="b"><span className="text-sm ">B</span></Avatar>
        </div>
        <div className="space-y-2">
            <div>
                <p className="text-base font-medium">Bigyan</p>
                <p className="text-sm text-gray-700">It is a long established fact</p>
            </div>
            <p className="text-sm">is simplever since the pe specimen book. Itt only five centuries,</p>
              </div>
              <h5 className="text-sm font-normal">00</h5>
    </div>
  )
}
