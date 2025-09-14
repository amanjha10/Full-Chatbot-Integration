import { CiCirclePlus } from "react-icons/ci";
import PersonCard from "../components/chat/PersonCard";
import ChatMessage from "../components/chat/ChatMessage";
import { useState } from "react";

import { useAdminChat } from "../hooks/useAdminChat";
import { useCompany } from "../context-provider/CompanyProvider";

export default function Chat() {
  const [messageText, setMessageText] = useState("");
  const { companyId } = useCompany();

  const {
    handoffSessions,
    selectedSession,
    messages,
    loading,
    loadingMessages,
    sendingMessage,
    isConnected,
    sendMessage,
    selectSession,
    loadHandoffSessions,
    refreshMessages,
    contextHolder
  } = useAdminChat();

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 60) {
      return `${diffMins}m`;
    } else {
      const diffHours = Math.floor(diffMins / 60);
      return `${diffHours}h`;
    }
  };

  const handleSendMessage = async () => {
    if (!messageText.trim() || !selectedSession) return;

    try {
      await sendMessage(selectedSession.session_id, messageText.trim());
      setMessageText("");
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="pt-4 space-y-4">
      {contextHolder}

      {/* Header */}
      <div className="bg-white rounded-lg p-4 shadow-sm border">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Admin Chat Dashboard</h1>
            <p className="text-sm text-gray-600">Direct chat with escalated users • Company: {companyId}</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-medium text-purple-600">Admin Mode</p>
              <p className="text-xs text-gray-500">You can chat directly with users</p>
              {selectedSession && (
                <div className="flex items-center gap-1 mt-1">
                  <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <span className="text-xs text-gray-500">
                    {isConnected ? 'Real-time connected' : 'Offline'}
                  </span>
                </div>
              )}
            </div>
            <button
              onClick={loadHandoffSessions}
              disabled={loading}
              className="bg-purple text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-700 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="flex gap-4 h-[600px]">

      <div className="basis-[25%] space-y-2 border-r pr-2 overflow-y-auto">
        {loading ? (
          <div className="text-center py-4">Loading sessions...</div>
        ) : handoffSessions.length === 0 ? (
          <div className="text-center py-4 text-gray-500">
            <p>No pending sessions</p>
            <p className="text-sm">When your company's chatbot users escalate to human, they will appear here</p>
            <p className="text-xs mt-1">Company: {companyId}</p>
          </div>
        ) : (
          handoffSessions.map((session) => (
            <PersonCard
              key={session.id}
              userName={session.user_name}
              lastMessage={session.message}
              time={formatTime(session.created_at)}
              isSelected={selectedSession?.id === session.id}
              onClick={() => selectSession(session)}
            />
          ))
        )}
      </div>
      <div className="flex flex-col flex-1 bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between pb-2">
          <div className="font-bold">
            {selectedSession
              ? `Chat with ${selectedSession.user_name}`
              : 'Select a session to start chatting'
            }
          </div>
          {selectedSession && (
            <button
              onClick={refreshMessages}
              className="text-sm text-purple-600 hover:text-purple-800 px-2 py-1 rounded"
              title="Refresh messages"
            >
              🔄 Refresh
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto space-y-4 mt-3 p-4">
          {loadingMessages ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
              <p className="text-gray-500 mt-2">Loading messages...</p>
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-4">💬</div>
              <p className="text-lg font-medium">
                {selectedSession ? 'No messages yet' : 'Select a session to view messages'}
              </p>
              <p className="text-sm mt-1">
                {selectedSession ? 'Start the conversation with your user!' : 'Choose a pending session from the left panel'}
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}
        </div>
        <div className="bg-white border-t p-4">

          <div className="flex items-center gap-3">
            <input
              type="file"
              style={{ display: "none" }}
              onChange={(e) => {
                console.log("file", e.target.files?.[0]);
              }}
              id="upload-file"
            />
            <label
              htmlFor="upload-file"
              className="cursor-pointer text-gray-400 hover:text-purple-600 transition-colors"
            >
              <CiCirclePlus size={28} />
            </label>

            <div className="flex-1 relative">
              <input
                type="text"
                placeholder={selectedSession ? "Type your message..." : "Select a session to start chatting"}
                className="w-full px-4 py-3 border border-gray-300 rounded-full outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500"
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                onKeyDown={handleKeyPress}
                disabled={!selectedSession || sendingMessage}
              />
            </div>

            <button
              className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-full font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-w-[80px]"
              onClick={handleSendMessage}
              disabled={!selectedSession || !messageText.trim() || sendingMessage}
            >
              {sendingMessage ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                </div>
              ) : (
                'Send'
              )}
            </button>
          </div>

          {selectedSession && (
            <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
              <span>💬 Chatting with {selectedSession.user_name}</span>
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                <span>{isConnected ? 'Real-time connected' : 'Offline'}</span>
              </div>
            </div>
          )}
        </div>
        </div>

      </div>
    </div>
  );
}