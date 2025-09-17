import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import {
  getPendingSessions,
  getSessionMessages
} from '../api/get';
import {
  sendAgentMessage,
  // assignSession,
  // resolveSession
} from '../api/post';
import type {
  PendingSessionData,
  ChatMessage
} from '../type/chat';
import { useCompany } from '../context-provider/CompanyProvider';
import { useAdminWebSocket } from './useAdminWebSocket';

// Utility function to create unique message key
const getMessageKey = (_msg: any) => {
  return `${_msg.id || 'no-id'}-${_msg.content}-${_msg.message_type}-${_msg.timestamp}`;
};

// Utility function to check if two messages are duplicates
const isDuplicateMessage = (msg1: any, msg2: any) => {
  if (msg1.id && msg2.id && msg1.id === msg2.id) return true;

  return (
    msg1.content === msg2.content &&
    msg1.message_type === msg2.message_type &&
    Math.abs(new Date(msg1.timestamp).getTime() - new Date(msg2.timestamp).getTime()) < 2000 // 2 second tolerance
  );
};

export const useAdminChat = () => {
  const { companyId } = useCompany();
  const [handoffSessions, setHandoffSessions] = useState<PendingSessionData[]>([]);
  const [selectedSession, setSelectedSession] = useState<PendingSessionData | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sendingMessage, setSendingMessage] = useState(false);
  const [messageApi, contextHolder] = message.useMessage();

  // WebSocket connection for real-time updates
  const { isConnected } = useAdminWebSocket(
    selectedSession?.session_id || null,
    {
      onMessageReceived: (newMessage) => {
        // Only add user messages from WebSocket (admin messages come from API)
        if (newMessage.message_type === 'user') {
          setMessages(prev => {
            // Check if message already exists to prevent duplicates
            const exists = prev.some(msg => isDuplicateMessage(msg, newMessage));
            if (!exists) {
              return [...prev, newMessage];
            }
            return prev;
          });
        }
      },
      onConnectionChange: (connected) => {
        console.log('Admin WebSocket connection:', connected ? 'Connected' : 'Disconnected');
      }
    }
  );

  // Load handoff sessions (pending escalations) - uses admin dashboard API with built-in company isolation
  const loadHandoffSessions = useCallback(async () => {
    try {
      setLoading(true);
      const response = await getPendingSessions();
      setHandoffSessions(response.data || []);
    } catch (error: any) {
      console.error('Failed to load handoff sessions:', error);
      messageApi.error('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  }, [messageApi]);

  // Load messages for a session
  const loadSessionMessages = useCallback(async (sessionId: string) => {
    if (!companyId) {
      console.warn('No company ID available for loading messages');
      messageApi.error('Company ID not available');
      return;
    }

    try {
      setLoadingMessages(true);
      const response = await getSessionMessages(sessionId, companyId);
      // The chat history API returns { messages: [...] } structure
      const newMessages = response.data.messages || [];

      // Deduplicate messages using utility function
      const uniqueMessages = newMessages.filter((newMsg: any, index: number, arr: any[]) => {
        // Remove duplicates within the new messages array
        const firstIndex = arr.findIndex((msg: any) => isDuplicateMessage(msg, newMsg));
        return firstIndex === index;
      });

      setMessages(uniqueMessages);
    } catch (error: any) {
      console.error('Failed to load messages:', error);
      messageApi.error('Failed to load messages');
    } finally {
      setLoadingMessages(false);
    }
  }, [companyId, messageApi]);

  // Send message as admin
  const sendMessage = useCallback(async (sessionId: string, messageText: string) => {
    try {
      setSendingMessage(true);
      const response = await sendAgentMessage({
        session_id: sessionId,
        message: messageText
      });

      // Add admin's message to the list (backend handles WebSocket broadcast)
      if (response.data.chat_message) {
        const adminMessage = {
          ...response.data.chat_message,
          message_type: 'agent',
          sender_name: 'Admin'
        };
        setMessages(prev => {
          // Check for duplicates before adding
          const exists = prev.some(msg => isDuplicateMessage(msg, adminMessage));
          if (!exists) {
            return [...prev, adminMessage];
          }
          return prev;
        });
      }

      // Don't send via WebSocket - backend already handles WebSocket broadcast

      messageApi.success('Message sent successfully');
      return response.data;
    } catch (error: any) {
      console.error('Failed to send message:', error);
      messageApi.error('Failed to send message');
      throw error;
    } finally {
      setSendingMessage(false);
    }
  }, [messageApi]);

  // Select a session and load its messages
  const selectSession = useCallback(async (session: PendingSessionData) => {
    // Clear messages when switching sessions to prevent mixing
    setMessages([]);
    setSelectedSession(session);
    await loadSessionMessages(session.session_id);
  }, [loadSessionMessages]);



  // Refresh current session messages
  const refreshMessages = useCallback(() => {
    if (selectedSession) {
      setMessages([]);
      loadSessionMessages(selectedSession.session_id);
    }
  }, [selectedSession, loadSessionMessages]);

  // Initialize data on mount
  useEffect(() => {
    loadHandoffSessions();
  }, [loadHandoffSessions]);

  return {
    // Data
    handoffSessions,
    selectedSession,
    messages,

    // Loading states
    loading,
    loadingMessages,
    sendingMessage,

    // WebSocket
    isConnected,

    // Actions
    sendMessage,
    selectSession,
    loadHandoffSessions,
    loadSessionMessages,
    refreshMessages,

    // UI
    contextHolder
  };
};
