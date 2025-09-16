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
  is_cancelled?: boolean;
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
        response?: { data?: { error?: string; can_create?: boolean; current_count?: number; max_allowed?: number; plan_name?: string; upgrade_needed?: boolean; is_cancelled?: boolean } };
        message?: string;
      };

      // If it's a 403 but has limit data, use that data
      if (error?.response?.data && typeof error.response.data === 'object') {
        const data = error.response.data;
        if (data.hasOwnProperty('can_create')) {
          setLimits(data as AgentLimits);
          return;
        }
      }

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
      if (limits?.is_cancelled) {
        // Show cancellation message
        messageApi.error({
          content: `${limits.error}\n${limits.suggestion}`,
          duration: 8,
        });
      } else {
        // Show regular upgrade message
        messageApi.warning({
          content: `${limits.error}\n${limits.suggestion}\nCurrent usage: ${limits.current_count}/${limits.max_allowed} agents`,
          duration: 6,
        });
      }
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
      ? limits.is_cancelled
        ? `${limits.current_count} agents`
        : `${limits.current_count}/${limits.max_allowed}`
      : null,
    planName: limits?.plan_name || null,
  };
};
