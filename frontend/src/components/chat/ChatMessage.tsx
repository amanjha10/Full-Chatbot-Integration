import { Avatar } from "antd";
import type { ChatMessage as ChatMessageType } from "../../type/chat";

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isAgent = message.message_type === 'agent';
  const isUser = message.message_type === 'user';
  const isBot = message.message_type === 'bot';

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    });
  };

  const getInitials = (name: string) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const getSenderName = () => {
    if (isAgent) return message.sender_name || 'Agent';
    if (isUser) return message.sender_name || 'User';
    if (isBot) return 'SpellBot';
    return 'Unknown';
  };

  const getAvatarColor = () => {
    if (isAgent) return '#52c41a'; // Green for agent
    if (isUser) return '#1890ff';  // Blue for user
    if (isBot) return '#722ed1';   // Purple for bot
    return '#d9d9d9';
  };

  const getMessageBgColor = () => {
    if (isAgent) return 'bg-green-500 text-white';
    if (isUser) return 'bg-white text-gray-900';
    if (isBot) return 'bg-purple-500 text-white';
    return 'bg-gray-200 text-gray-900';
  };

  return (
    <div className={`flex items-start gap-3 ${isAgent ? 'justify-end' : 'justify-start'}`}>
      {!isAgent && (
        <Avatar 
          size={32} 
          style={{ backgroundColor: getAvatarColor(), flexShrink: 0 }}
        >
          <span className="text-xs font-medium">
            {getInitials(getSenderName())}
          </span>
        </Avatar>
      )}
      
      <div className={`flex flex-col ${isAgent ? 'items-end' : 'items-start'} max-w-xs lg:max-w-md`}>
        <div className={`px-4 py-2 rounded-lg shadow ${getMessageBgColor()}`}>
          {/* File attachment */}
          {message.file_url && message.file_name && (
            <div className="mb-2">
              <div className="flex items-center gap-2 p-2 bg-black bg-opacity-10 rounded">
                <span className="text-sm">📎</span>
                <a 
                  href={message.file_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-sm underline hover:no-underline"
                >
                  {message.file_name}
                </a>
              </div>
            </div>
          )}
          
          {/* Message content */}
          <p className="text-sm whitespace-pre-wrap break-words">
            {message.content}
          </p>
        </div>
        
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-500">
            {getSenderName()}
          </span>
          <span className="text-xs text-gray-400">
            {formatTime(message.timestamp)}
          </span>
        </div>
      </div>
      
      {isAgent && (
        <Avatar 
          size={32} 
          style={{ backgroundColor: getAvatarColor(), flexShrink: 0 }}
        >
          <span className="text-xs font-medium">
            {getInitials(getSenderName())}
          </span>
        </Avatar>
      )}
    </div>
  );
}
