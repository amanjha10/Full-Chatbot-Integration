import { MdAssignmentAdd } from "react-icons/md";
interface CardProps{
  title:string,
  count:number
}
export default function Card({title,count}:CardProps) {
  return (
    <div className="p-3 bg-white rounded-md shadow-xl h-[120px] transition hover:translate-y-[-2px] duration-150 ease-in-out">
        <div className="flex items-center justify-between">
            <p className="text-base font-medium pb-6">{title}</p>
            <span><MdAssignmentAdd size={25}/></span>
        </div>
        <h4 className="text-2xl font-bold text-black">{count}</h4>
    </div>
  )
}
