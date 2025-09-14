import { Avatar } from "antd";

// Simple PersonCard for the basic layout
export default function PersonCard({
  userName = "Bigyan",
  lastMessage = "It is a long established fact",
  time = "00",
  isSelected = false,
  onClick
}: {
  userName?: string;
  lastMessage?: string;
  time?: string;
  isSelected?: boolean;
  onClick?: () => void;
}) {
  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const truncateMessage = (message: string, maxLength: number = 80) => {
    if (message.length <= maxLength) return message;
    return message.substring(0, maxLength) + '...';
  };

  return (
    <div
      className={`rounded-md p-4 flex gap-3 min-h-[120px] w-full cursor-pointer transition-colors ${
        isSelected ? 'bg-blue-100 border-2 border-blue-300' : 'bg-gray-200 hover:bg-gray-300'
      }`}
      onClick={onClick}
    >
      <div className="flex-shrink-0 w-[35px] h-[35px]">
        <Avatar size={35}>
          <span className="text-sm">
            {getInitials(userName)}
          </span>
        </Avatar>
      </div>

      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex justify-between items-start">
          <p className="text-base font-medium text-gray-900 truncate">{userName}</p>
          <span className="text-xs text-gray-500 flex-shrink-0 ml-2">{time}</span>
        </div>

        <div className="text-sm text-gray-600">
          <p className="break-words line-clamp-3 leading-relaxed">
            {truncateMessage(lastMessage, 100)}
          </p>
        </div>
      </div>
    </div>
  );
}
