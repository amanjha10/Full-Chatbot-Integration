import { useEffect, useRef, useState } from 'react';
import { useCompany } from '../context-provider/CompanyProvider';

interface AdminWebSocketOptions {
  onMessageReceived?: (message: any) => void;
  onConnectionChange?: (connected: boolean) => void;
}

export const useAdminWebSocket = (sessionId: string | null, options: AdminWebSocketOptions = {}) => {
  const { companyId } = useCompany();
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const { onMessageReceived, onConnectionChange } = options;

  useEffect(() => {
    if (!sessionId || !companyId) {
      return;
    }

    // Create WebSocket connection for the specific session
    const wsUrl = `ws://localhost:8000/ws/chat/${companyId}/${sessionId}/`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      onConnectionChange?.(true);
      console.log(`Admin WebSocket connected for session ${sessionId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Admin WebSocket message received:', data);

        // Handle different message types
        switch (data.type) {
          case 'chat_message':
            // New message received - only process user messages to avoid duplicates
            if (data.sender_type === 'user' && onMessageReceived) {
              console.log('Processing user message from WebSocket:', data.message);
              onMessageReceived({
                id: data.message_id,
                content: data.message,
                message_type: data.sender_type,
                timestamp: data.timestamp,
                sender_name: data.sender_name,
                file_url: data.file_url,
                file_name: data.file_name,
                file_type: data.file_type
              });
            } else if (data.sender_type === 'agent') {
              console.log('Ignoring agent message from WebSocket to prevent duplicates');
            }
            break;

          case 'agent_joined':
            console.log('Agent joined the session:', data.agent_info);
            break;

          case 'typing':
            console.log('Typing indicator:', data);
            break;

          case 'connection_established':
            console.log('WebSocket connection established:', data.message);
            break;

          default:
            console.log('Unknown WebSocket message type:', data.type);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      onConnectionChange?.(false);
      console.log('Admin WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('Admin WebSocket error:', error);
      setIsConnected(false);
      onConnectionChange?.(false);
    };

    // Cleanup on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [sessionId, companyId, onMessageReceived, onConnectionChange]);

  // Send message via WebSocket (for real-time updates)
  const sendWebSocketMessage = (message: string, senderName: string = 'Admin') => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat_message',
        message: message,
        sender_type: 'agent', // Admin messages are treated as agent messages
        sender_name: senderName,
        session_id: sessionId
      }));
    }
  };

  return {
    isConnected,
    sendWebSocketMessage
  };
};
