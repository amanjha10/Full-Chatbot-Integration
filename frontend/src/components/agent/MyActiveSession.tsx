import { Badge, Button, message, Modal } from "antd";
import { HiRefresh } from "react-icons/hi";
import { IoMdCheckboxOutline } from "react-icons/io";
import { IoChatbubbles, IoEye } from "react-icons/io5";
import { useState } from "react";
import { axiosClient } from "../../config/axiosConfig";
import RealTimeChat from "../chat/RealTimeChat";
import { useCompanyId } from "../../context-provider/CompanyProvider";
import { useAgentRealTimeData } from "../../hooks/useAgentWebSocket";

interface ActiveSessionData {
  id: number;
  session_id: string;
  user_name: string;
  user_phone: string;
  last_message: string;
  started_at: string;
  message_count: number;
}

export default function MyActiveSession() {
  const [completingSession, setCompletingSession] = useState<number | null>(
    null
  );
  const [selectedSession, setSelectedSession] =
    useState<ActiveSessionData | null>(null);
  const [chatModalVisible, setChatModalVisible] = useState(false);
  const companyId = useCompanyId();

  // Use the new real-time hook instead of SWR directly
  const {
    activeSessions,
    isConnected,
    sessionsLoading,
    refreshActiveSessions,
  } = useAgentRealTimeData();

  const handleRefresh = () => {
    refreshActiveSessions();
  };

  const handleCompleteSession = async (sessionId: number) => {
    setCompletingSession(sessionId);
    try {
      await axiosClient.post("/agent-dashboard/complete-session/", {
        session_id: sessionId,
      });

      message.success("Session completed successfully");
      refreshActiveSessions(); // Refresh the list
    } catch (error: unknown) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to complete session";
      message.error(errorMessage);
    } finally {
      setCompletingSession(null);
    }
  };

  const handleOpenChat = (session: ActiveSessionData) => {
    setSelectedSession(session);
    setChatModalVisible(true);
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="p-4 space-y-4 mb-4 bg-white rounded-md shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <IoChatbubbles size={20} />
          <p className="text-lg font-bold">My Active Sessions</p>
          {/* WebSocket connection indicator */}
          <span
            className={`text-xs px-2 py-1 rounded ${
              isConnected
                ? "bg-green-100 text-green-800"
                : "bg-red-100 text-red-800"
            }`}
          >
            {isConnected ? "🟢 Live" : "🔴 Offline"}
          </span>
        </div>
        <Badge
          count={activeSessions?.length || 0}
          color="#652d90"
          showZero
          offset={[-77, -9]}
        >
          <Button
            icon={<HiRefresh />}
            size="small"
            type="primary"
            className="!bg-yellow"
            onClick={handleRefresh}
            loading={sessionsLoading}
          >
            {isConnected ? "Refresh" : "Manual Refresh"}
          </Button>
        </Badge>
      </div>

      <div className="max-h-80 overflow-y-auto space-y-3">
        {sessionsLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="bg-gray-100 rounded-md p-3 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : activeSessions && activeSessions.length > 0 ? (
          activeSessions?.map((session: ActiveSessionData) => (
            <div
              key={session.id}
              className="w-full border border-gray-200 rounded-md bg-gray-50 p-3"
            >
              <div className="flex justify-between mb-3">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <h2 className="text-base font-bold text-gray-900">
                      {session.user_name}
                    </h2>
                    <span className="text-sm text-gray-500">
                      ({session.user_phone})
                    </span>
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {session.message_count} messages
                    </span>
                  </div>
                  <p className="text-sm font-normal text-gray-600 line-clamp-2">
                    {session.last_message}
                  </p>
                </div>
                <p className="text-sm font-normal text-gray-500 whitespace-nowrap">
                  {formatTime(session.started_at)}
                </p>
              </div>

              <div className="flex gap-2 items-center justify-end">
                <Button
                  type="primary"
                  icon={<IoChatbubbles size={13} />}
                  className="!w-[65px] !h-[28px] !text-sm !bg-purple !rounded-lg"
                  onClick={() => handleOpenChat(session)}
                >
                  Chat
                </Button>
                <Button
                  type="primary"
                  icon={<IoMdCheckboxOutline size={13} />}
                  className="!w-[100px] px-2 !h-[28px] !rounded-lg !text-sm !hover:bg-green-600 !bg-green-500"
                  loading={completingSession === session.id}
                  onClick={() => handleCompleteSession(session.id)}
                >
                  Complete
                </Button>
                <Button
                  type="primary"
                  icon={<IoEye size={13} />}
                  className="!w-[65px] !h-[28px] !text-sm !bg-slate-500 !hover:bg-slate-600 !rounded-lg"
                  onClick={() => handleOpenChat(session)}
                >
                  View
                </Button>
              </div>
            </div>
          ))
        ) : (
          <div className="h-20 flex items-center justify-center">
            <p className="text-center text-base font-semibold text-gray-500">
              No Active Sessions
            </p>
          </div>
        )}
      </div>

      {/* Chat Modal */}
      <Modal
        title={`Chat with ${selectedSession?.user_name}`}
        open={chatModalVisible}
        onCancel={() => setChatModalVisible(false)}
        width={800}
        footer={null}
        styles={{ body: { padding: 0, height: "600px" } }}
      >
        {selectedSession && (
          <RealTimeChat
            sessionId={selectedSession.session_id}
            companyId={companyId || "DEFAULT_COMPANY"}
            userType="agent"
            userName="Agent"
            onClose={() => setChatModalVisible(false)}
          />
        )}
      </Modal>
    </div>
  );
}
