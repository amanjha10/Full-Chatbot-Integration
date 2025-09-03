import { useState, useEffect } from "react";
import { checkAgentLimits } from "../api/get";
import { useMessageContext } from "../context-provider/MessageProvider";

interface AgentLimits {
  can_create: boolean;
  current_count: number;
  max_allowed: number;
  plan_name: string;
  message?: string;
  error?: string;
  suggestion?: string;
  upgrade_needed?: boolean;
  current_plan?: string;
}

export const useAgentLimits = () => {
  const [limits, setLimits] = useState<AgentLimits | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { messageApi } = useMessageContext();

  const fetchLimits = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await checkAgentLimits();
      setLimits(response.data);
    } catch (err: unknown) {
      const error = err as {
        response?: { data?: { error?: string } };
        message?: string;
      };
      const errorMessage =
        error?.response?.data?.error ||
        error?.message ||
        "Failed to check agent limits";
      setError(errorMessage);
      console.error("Error fetching agent limits:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLimits();
  }, []);

  const showUpgradeMessage = () => {
    if (limits?.upgrade_needed && limits?.suggestion) {
      messageApi.warning({
        content: `${limits.error}\n${limits.suggestion}\nCurrent usage: ${limits.current_count}/${limits.max_allowed} agents`,
        duration: 6,
      });
    }
  };

  return {
    limits,
    loading,
    error,
    fetchLimits,
    showUpgradeMessage,
    canCreateAgent: limits?.can_create || false,
    currentUsage: limits
      ? `${limits.current_count}/${limits.max_allowed}`
      : null,
    planName: limits?.plan_name || null,
  };
};
