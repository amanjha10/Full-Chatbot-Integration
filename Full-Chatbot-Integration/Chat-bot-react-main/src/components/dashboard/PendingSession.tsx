import { Button, Tag, message, Select } from "antd";
import { useForm } from "react-hook-form";
import { HiRefresh } from "react-icons/hi";
import { MdOutlineAccessTimeFilled } from "react-icons/md";
import AppSelect from "../../share/form/AppSelect";
import { TiUserAddOutline } from "react-icons/ti";
import { agentList } from "../../constant";
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

interface Agent {
  id: number;
  name: string;
  email: string;
  status: "AVAILABLE" | "BUSY" | "OFFLINE";
}

export default function PendingSession() {
  const { control } = useForm();
  const [assigningSession, setAssigningSession] = useState<number | null>(null);
  const [selectedAgents, setSelectedAgents] = useState<{
    [key: number]: number;
  }>({});

  // Fetch pending sessions (FIFO order - oldest first)
  const {
    data: pendingSessions,
    isLoading: sessionsLoading,
    mutate: mutateSessions,
  } = useSWR<PendingSessionData[]>("/admin-dashboard/pending-sessions/");

  // Fetch available agents
  const { data: agents, isLoading: agentsLoading } = useSWR<Agent[]>(
    "/admin-dashboard/available-agents/"
  );

  const handleRefresh = () => {
    mutateSessions();
  };

  const handleAssignSession = async (sessionId: number) => {
    const agentId = selectedAgents[sessionId];
    if (!agentId) {
      message.error("Please select an agent first");
      return;
    }

    setAssigningSession(sessionId);
    try {
      await axiosClient.post("/admin-dashboard/assign-session/", {
        session_id: sessionId,
        agent_id: agentId,
      });

      message.success("Session assigned successfully");
      mutateSessions(); // Refresh the list

      // Clear the selected agent for this session
      setSelectedAgents((prev) => {
        const updated = { ...prev };
        delete updated[sessionId];
        return updated;
      });
    } catch (error: any) {
      message.error(error?.response?.data?.error || "Failed to assign session");
    } finally {
      setAssigningSession(null);
    }
  };

  const handleAgentSelect = (sessionId: number, agentId: number) => {
    setSelectedAgents((prev) => ({
      ...prev,
      [sessionId]: agentId,
    }));
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

  if (sessionsLoading) {
    return (
      <div className="p-4 bg-white rounded-md space-y-5 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <MdOutlineAccessTimeFilled size={20} />
            <p className="text-lg font-bold">Pending Sessions</p>
          </div>
          <Button
            icon={<HiRefresh />}
            size="small"
            type="primary"
            className="!bg-yellow"
            loading
          >
            Refresh
          </Button>
        </div>
        <div className="space-y-3">
          {[1, 2].map((i) => (
            <div
              key={i}
              className="w-full bg-gray-100 rounded-xl p-7 border border-gray-300 animate-pulse"
            >
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-white rounded-md space-y-5 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <MdOutlineAccessTimeFilled size={20} />
          <p className="text-lg font-bold">
            Pending Sessions ({pendingSessions?.length || 0})
          </p>
        </div>
        <Button
          icon={<HiRefresh />}
          size="small"
          type="primary"
          className="!bg-yellow"
          onClick={handleRefresh}
        >
          Refresh
        </Button>
      </div>

      <div className="max-h-96 overflow-y-auto space-y-3">
        {pendingSessions && pendingSessions.length > 0 ? (
          pendingSessions.map((session, index) => (
            <div
              key={session.id}
              className="w-full bg-gray-100 rounded-xl p-4 border border-gray-300 space-y-3"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-medium text-gray-600">
                      #{index + 1}
                    </span>
                    <span className="text-sm text-gray-500">
                      {session.user_name}
                    </span>
                    <span className="text-sm text-gray-500">
                      ({session.user_phone})
                    </span>
                    <span className="text-xs text-gray-400">
                      {formatWaitingTime(session.created_at)}
                    </span>
                  </div>
                  <p className="font-normal text-sm text-gray-700 max-w-[350px] line-clamp-2">
                    {session.message}
                  </p>
                </div>
                <div className="flex flex-col items-end gap-2">
                  <Tag color={getPriorityColor(session.priority)}>
                    {session.priority}
                  </Tag>
                </div>
              </div>

              <div className="flex gap-3 items-center">
                <Select
                  placeholder="Select Agent"
                  className="flex-1"
                  value={selectedAgents[session.id]}
                  onChange={(agentId) => handleAgentSelect(session.id, agentId)}
                  loading={agentsLoading}
                >
                  {agents
                    ?.filter((agent) => agent.status === "AVAILABLE")
                    .map((agent) => (
                      <Select.Option key={agent.id} value={agent.id}>
                        {agent.name} ({agent.email})
                      </Select.Option>
                    ))}
                </Select>
                <Button
                  type="primary"
                  className="!bg-yellow"
                  icon={<TiUserAddOutline size={16} />}
                  loading={assigningSession === session.id}
                  disabled={!selectedAgents[session.id]}
                  onClick={() => handleAssignSession(session.id)}
                >
                  Assign
                </Button>
              </div>
            </div>
          ))
        ) : (
          <div className="w-full bg-gray-50 rounded-xl p-8 border border-gray-200 text-center">
            <MdOutlineAccessTimeFilled
              size={48}
              className="mx-auto text-gray-300 mb-4"
            />
            <p className="text-gray-500 text-lg font-medium">
              No pending sessions
            </p>
            <p className="text-gray-400 text-sm">
              All conversations are being handled by agents
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
