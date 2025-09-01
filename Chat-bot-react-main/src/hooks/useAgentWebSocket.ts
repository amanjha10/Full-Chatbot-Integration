import { useEffect, useRef, useState, useCallback } from "react";
import useSWR from "swr";

interface AgentProfile {
  id: number;
  name: string;
  email: string;
  status: string;
  company_id: string;
}

interface WebSocketEventData {
  session_id?: string;
  agent_id?: number;
  message?: string;
  [key: string]: unknown;
}

interface UseAgentWebSocketOptions {
  onSessionAssigned?: (data: WebSocketEventData) => void;
  onChatMessage?: (data: WebSocketEventData) => void;
  onSessionUpdate?: (data: WebSocketEventData) => void;
}

export function useAgentWebSocket(
  agentId: number | null,
  options: UseAgentWebSocketOptions = {}
) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Memoize callbacks to prevent useEffect re-runs
  const { onSessionAssigned, onChatMessage, onSessionUpdate } = options;

  const handleSessionAssigned = useCallback(
    (data: WebSocketEventData) => {
      onSessionAssigned?.(data);
    },
    [onSessionAssigned]
  );

  const handleChatMessage = useCallback(
    (data: WebSocketEventData) => {
      onChatMessage?.(data);
    },
    [onChatMessage]
  );

  const handleSessionUpdate = useCallback(
    (data: WebSocketEventData) => {
      onSessionUpdate?.(data);
    },
    [onSessionUpdate]
  );

  useEffect(() => {
    if (!agentId) return;

    const wsUrl = `ws://localhost:8000/ws/agent/${agentId}/`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log(`Agent WebSocket connected for agent ${agentId}`);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Agent WebSocket message:", data);

      switch (data.type) {
        case "session_assigned":
          handleSessionAssigned(data.data);
          break;

        case "chat_message":
          handleChatMessage(data.data);
          break;

        case "session_update":
          handleSessionUpdate(data.data);
          break;

        case "connection_established":
          console.log("Agent dashboard connection established:", data.message);
          break;

        default:
          console.log("Unknown WebSocket message type:", data.type);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log(`Agent WebSocket disconnected for agent ${agentId}`);
    };

    ws.onerror = (error) => {
      console.error("Agent WebSocket error:", error);
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [agentId, handleSessionAssigned, handleChatMessage, handleSessionUpdate]);

  return { isConnected, wsRef };
}

export function useAgentRealTimeData() {
  const [agentProfile, setAgentProfile] = useState<AgentProfile | null>(null);

  // Fetch agent profile to get agent ID
  const { data: profileData } = useSWR<AgentProfile>(
    "/agent-dashboard/profile/"
  );

  // Fetch active sessions with auto-refresh
  const {
    data: activeSessions,
    mutate: refreshActiveSessions,
    isLoading: sessionsLoading,
  } = useSWR("/agent-dashboard/active-sessions/");

  // Fetch stats with auto-refresh
  const {
    data: stats,
    mutate: refreshStats,
    isLoading: statsLoading,
  } = useSWR("/agent-dashboard/stats/");

  // Set agent profile when data is available
  useEffect(() => {
    if (profileData) {
      setAgentProfile(profileData);
    }
  }, [profileData]);

  // WebSocket callbacks
  const handleSessionAssigned = useCallback(() => {
    console.log("New session assigned - refreshing data");
    refreshStats();
    refreshActiveSessions();
  }, [refreshStats, refreshActiveSessions]);

  const handleChatMessage = useCallback(() => {
    console.log("New chat message - refreshing active sessions");
    refreshActiveSessions();
  }, [refreshActiveSessions]);

  const handleSessionUpdate = useCallback(() => {
    console.log("Session update - refreshing data");
    refreshStats();
    refreshActiveSessions();
  }, [refreshStats, refreshActiveSessions]);

  // WebSocket connection for real-time updates
  const { isConnected } = useAgentWebSocket(agentProfile?.id || null, {
    onSessionAssigned: handleSessionAssigned,
    onChatMessage: handleChatMessage,
    onSessionUpdate: handleSessionUpdate,
  });

  return {
    agentProfile,
    activeSessions,
    stats,
    isConnected,
    sessionsLoading,
    statsLoading,
    refreshActiveSessions,
    refreshStats,
  };
}
