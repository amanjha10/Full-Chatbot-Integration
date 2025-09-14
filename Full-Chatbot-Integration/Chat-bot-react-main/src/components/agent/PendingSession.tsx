import { Badge, Button, message, Tag } from "antd";
import { HiRefresh } from "react-icons/hi";
import { MdOutlineAccessTimeFilled } from "react-icons/md";
import { FaCheck } from "react-icons/fa";
import { useState } from "react";
import useSWR from "swr";
import { axiosClient } from "../../config/axiosConfig";

interface PendingSessionData {
  id: number;
  session_id: string;
  user_name: string;
  user_phone: string;
  message: string;
  priority: "LOW" | "MEDIUM" | "HIGH";
  created_at: string;
  waiting_time: string;
}

export default function PendingSession() {
  const [acceptingSession, setAcceptingSession] = useState<number | null>(null);

  // Fetch pending sessions assigned to this agent
  const {
    data: pendingSessions,
    isLoading,
    mutate,
  } = useSWR<PendingSessionData[]>("/agent-dashboard/pending-sessions/");

  const handleRefresh = () => {
    mutate();
  };

  const handleAcceptSession = async (sessionId: number) => {
    setAcceptingSession(sessionId);
    try {
      await axiosClient.post("/agent-dashboard/accept-session/", {
        session_id: sessionId,
      });

      message.success("Session accepted successfully");
      mutate(); // Refresh the list
    } catch (error: any) {
      message.error(error?.response?.data?.error || "Failed to accept session");
    } finally {
      setAcceptingSession(null);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "HIGH":
        return "red";
      case "MEDIUM":
        return "orange";
      case "LOW":
        return "green";
      default:
        return "default";
    }
  };

  const formatWaitingTime = (createdAt: string) => {
    const now = new Date();
    const created = new Date(createdAt);
    const diffMs = now.getTime() - created.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else {
      const diffHours = Math.floor(diffMins / 60);
      return `${diffHours}h ${diffMins % 60}m ago`;
    }
  };

  return (
    <div className="p-4 bg-white space-y-4 mb-4 rounded-md shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <MdOutlineAccessTimeFilled size={20} />
          <p className="text-lg font-bold">Pending Sessions</p>
        </div>
        <Badge
          count={pendingSessions?.length || 0}
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
            loading={isLoading}
          >
            Refresh
          </Button>
        </Badge>
      </div>

      <div className="max-h-80 overflow-y-auto space-y-3">
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="bg-gray-100 rounded-lg p-4 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            ))}
          </div>
        ) : pendingSessions && pendingSessions.length > 0 ? (
          pendingSessions.map((session) => (
            <div
              key={session.id}
              className="bg-gray-50 rounded-lg p-4 border space-y-3"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-medium text-gray-900">
                      {session.user_name}
                    </span>
                    <span className="text-sm text-gray-500">
                      ({session.user_phone})
                    </span>
                    <span className="text-xs text-gray-400">
                      {formatWaitingTime(session.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2 mb-2">
                    {session.message}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <Tag color={getPriorityColor(session.priority)}>
                    {session.priority}
                  </Tag>
                </div>
              </div>

              <div className="flex justify-end">
                <Button
                  type="primary"
                  size="small"
                  icon={<FaCheck size={14} />}
                  loading={acceptingSession === session.id}
                  onClick={() => handleAcceptSession(session.id)}
                  className="!bg-green-600 hover:!bg-green-700"
                >
                  Accept
                </Button>
              </div>
            </div>
          ))
        ) : (
          <div className="h-20 flex items-center justify-center">
            <p className="text-center text-base font-semibold text-gray-500">
              No Pending Sessions
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
