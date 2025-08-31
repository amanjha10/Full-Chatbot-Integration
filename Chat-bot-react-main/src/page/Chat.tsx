import { CiCirclePlus } from "react-icons/ci";
import PersonCard from "../components/chat/PersonCard";
import { useState } from "react";
import { IoMdCloseCircle } from "react-icons/io";

export default function Chat() {
  const [fileName, setFileName] = useState<string | undefined>(undefined);
  return (
    <div className="flex gap-4 pt-4 h-[600px]">
      <div className="basis-[25%] space-y-2 border-r pr-2 overflow-y-auto">
        <PersonCard />
        <PersonCard />
        <PersonCard />
        <PersonCard />
      </div>
      <div className="flex flex-col flex-1 bg-gray-50 rounded-lg p-4">
        <div className="font-bold  pb-2">Chat with Bigyan</div>
        <div className="flex-1 overflow-y-auto space-y-3 mt-3">
          <div className="flex items-start">
            <div className="bg-white shadow px-3 py-2 rounded-xl max-w-xs">
              Hey, how are you?
            </div>
          </div>

          {/* Me */}
          <div className="flex justify-end">
            <div className="bg-purple text-white shadow px-3 py-2 rounded-xl max-w-xs">
              I’m good, thanks! What about you?
            </div>
          </div>

          <div className="flex items-start">
            <div className="bg-white shadow px-3 py-2 rounded-xl max-w-xs">
              I’m doing great
            </div>
          </div>

          <div className="flex justify-end">
            <div className="bg-purple text-white shadow px-3 py-2 rounded-xl max-w-xs">
              Awesome! Let’s meet tomorrow.
            </div>
          </div>
        </div>
        <div className="bg-gray-200 rounded-3xl px-4 mt-3 py-3">
{fileName && <div className="relative"><p className="text-sm font-normal text-gray-400">{fileName}</p><div className="absolute  bottom-3 left-[16%] cursor-pointer" onClick={()=>setFileName(undefined)}><IoMdCloseCircle size={15} className="text-gray-500"/></div></div>}
 <div className=" flex items-center gap-2">
          <input
            type="file"
            style={{ display: "none" }}
            onChange={(e) => {
              console.log("file", e.target.files?.[0]);
              setFileName(e.target.files?.[0]?.name)
            }}
            id={`upload-${name}`}
          />
          <label
            htmlFor={`upload-${name}`}
            className="cursor-pointer   flex items-center justify-center rounded-full "
          >
            <CiCirclePlus size={25} />
          </label>

          <input
            type="text"
            placeholder="Type a message..."
            className="flex-1  rounded-lg px-3 py-2 outline-none focus:ring-0"
          />  
          <button className="bg-yellow text-white px-4 py-2 rounded-lg">
            Send
          </button>
        </div>
        </div>
       
      </div>
    </div>
  );
}
