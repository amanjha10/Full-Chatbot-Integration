import React, { useState, useEffect, useRef } from 'react';
import { Button, Input, Upload, message, Spin } from 'antd';
import { SendOutlined, PaperClipOutlined } from '@ant-design/icons';
import type { UploadFile } from 'antd/es/upload/interface';

interface ChatMessage {
  id: string;
  type: 'user' | 'agent' | 'system';
  content: string;
  timestamp: string;
  sender_name?: string;
  file_url?: string;
  file_name?: string;
}

interface RealTimeChatProps {
  sessionId: string;
  companyId: string;
  userType: 'agent' | 'user';
  userName?: string;
  onClose?: () => void;
}

export default function RealTimeChat({ 
  sessionId, 
  companyId, 
  userType, 
  userName,
  onClose 
}: RealTimeChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch chat history
  const fetchChatHistory = React.useCallback(async () => {
    if (userType !== 'agent') return;
    
    try {
      setLoadingHistory(true);
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(
        `http://127.0.0.1:8001/api/human-handoff/agent/sessions/${sessionId}/messages/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        const chatMessages: ChatMessage[] = data.messages.map((msg: {
          id: number;
          message_type: string;
          content: string;
          timestamp: string;
        }) => ({
          id: msg.id.toString(),
          type: msg.message_type === 'user' ? 'user' : msg.message_type === 'bot' ? 'agent' : 'system',
          content: msg.content,
          timestamp: msg.timestamp,
          sender_name: msg.message_type === 'user' ? (data.session.user_profile?.name || 'User') : 'Bot'
        }));
        
        setMessages(chatMessages);
        console.log('Chat history loaded:', chatMessages.length, 'messages');
      } else {
        console.error('Failed to fetch chat history:', response.status);
        message.error('Failed to load chat history');
      }
    } catch (error) {
      console.error('Error fetching chat history:', error);
      message.error('Error loading chat history');
    } finally {
      setLoadingHistory(false);
    }
  }, [sessionId, userType]);

  // Load chat history when component mounts
  useEffect(() => {
    fetchChatHistory();
  }, [fetchChatHistory]);

  // Initialize WebSocket connection
  useEffect(() => {
    const wsUrl = `ws://localhost:8000/ws/chat/${companyId}/${sessionId}/`;
    console.log('Attempting WebSocket connection to:', wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected successfully');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        
        switch (data.type) {
          case 'chat_message':
            setMessages(prev => [...prev, {
              id: data.message_id || Date.now().toString(),
              type: data.sender_type,
              content: data.message,
              timestamp: data.timestamp,
              sender_name: data.sender_name,
              file_url: data.file_url,
              file_name: data.file_name
            }]);
            break;
            
          case 'typing_indicator':
            if (data.sender_type !== userType) {
              setIsTyping(data.is_typing);
            }
            break;
            
          case 'system_message':
            setMessages(prev => [...prev, {
              id: Date.now().toString(),
              type: 'system',
              content: data.message,
              timestamp: data.timestamp
            }]);
            break;
            
          case 'connection_established':
            console.log('WebSocket connection confirmed:', data.message);
            break;
            
          case 'error':
            message.error(data.message);
            break;
            
          default:
            console.log('Unknown WebSocket message type:', data.type);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      message.error('Connection error occurred');
    };

    return () => {
      ws.close();
    };
  }, [sessionId, companyId, userType]);

  // Send message
  const sendMessage = async () => {
    if (!inputMessage.trim() && fileList.length === 0) return;
    
    setLoading(true);
    
    try {
      // For agents, use the backend API instead of direct WebSocket
      if (userType === 'agent') {
        const token = localStorage.getItem('access_token');
        
        // Handle file upload if present
        let fileUrl = '';
        let fileName = '';
        
        if (fileList.length > 0) {
          const formData = new FormData();
          formData.append('file', fileList[0].originFileObj as File);
          formData.append('session_id', sessionId);
          
          const uploadResponse = await fetch('http://127.0.0.1:8001/api/human-handoff/agent/upload/', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
            body: formData
          });
          
          if (uploadResponse.ok) {
            const uploadData = await uploadResponse.json();
            fileUrl = uploadData.file_url;
            fileName = uploadData.original_name;
          } else {
            throw new Error('Failed to upload file');
          }
        }
        
        const response = await fetch('http://127.0.0.1:8001/api/human-handoff/agent/send-message/', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: sessionId,
            message: inputMessage.trim(),
            file_url: fileUrl || undefined,
            file_name: fileName || undefined
          }),
        });

        if (response.ok) {
          const data = await response.json();
          // Add message to local state immediately
          const newMessage: ChatMessage = {
            id: data.chat_message.id.toString(),
            type: 'agent',
            content: data.chat_message.content,
            timestamp: data.chat_message.timestamp,
            sender_name: userName || 'Agent',
            file_url: fileUrl || undefined,
            file_name: fileName || undefined
          };
          setMessages(prev => [...prev, newMessage]);
          
          // Also send via WebSocket for real-time updates to user
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              type: 'chat_message',
              message: inputMessage.trim(),
              sender_type: 'agent',
              sender_name: userName || 'Agent',
              file_url: fileUrl || undefined,
              file_name: fileName || undefined
            }));
          }
        } else {
          const errorData = await response.text();
          console.error('Agent API Error Response:', errorData);
          throw new Error(`Failed to send message via API: ${response.status} - ${errorData}`);
        }
      } else {
        // For users, use direct WebSocket
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          message.error('Connection not available');
          return;
        }
        
        // Handle file upload if present
        let fileUrl = '';
        let fileName = '';
      
        if (fileList.length > 0) {
          const formData = new FormData();
          formData.append('file', fileList[0].originFileObj as File);
          formData.append('session_id', sessionId);
          
          // For users, use the chatbot upload endpoint
          const uploadEndpoint = 'http://127.0.0.1:8001/api/chatbot/upload/';
          
          // Add company_id for user uploads
          formData.append('company_id', companyId);
          
          const headers: Record<string, string> = {};
          
          const response = await fetch(uploadEndpoint, {
            method: 'POST',
            headers,
            body: formData
          });
          
          if (response.ok) {
            const result = await response.json();
            fileUrl = result.file_url;
            fileName = result.original_name;
          } else {
            throw new Error('File upload failed');
          }
        }

        // Send message via WebSocket
        wsRef.current.send(JSON.stringify({
          type: 'chat_message',
          message: inputMessage.trim(),
          sender_type: userType,
          sender_name: userName || 'User',
          file_url: fileUrl,
          file_name: fileName,
          session_id: sessionId
        }));
      }

      // Clear input
      setInputMessage('');
      setFileList([]);
      
    } catch (err) {
      console.error('Error sending message:', err);
      message.error('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  // Handle typing indicator
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputMessage(e.target.value);
    
    // Send typing indicator
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'typing_indicator',
        is_typing: true,
        sender_type: userType
      }));
      
      // Clear previous timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      
      // Set timeout to stop typing indicator
      typingTimeoutRef.current = setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'typing_indicator',
            is_typing: false,
            sender_type: userType
          }));
        }
      }, 1000);
    }
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b bg-gray-50">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="font-medium">
            {userType === 'agent' ? `Chat with User` : 'Support Chat'}
          </span>
        </div>
        {onClose && (
          <Button type="text" onClick={onClose}>×</Button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {loadingHistory ? (
          <div className="flex justify-center items-center h-full">
            <Spin size="large" />
            <span className="ml-2">Loading chat history...</span>
          </div>
        ) : (
          <>
            {messages.length === 0 ? (
              <div className="flex justify-center items-center h-full text-gray-500">
                No messages yet. Start the conversation!
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.type === userType ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    msg.type === 'system' 
                      ? 'bg-gray-100 text-gray-600 text-center text-sm'
                      : msg.type === userType
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}>
                    {msg.type !== 'system' && msg.sender_name && (
                      <div className="text-xs opacity-75 mb-1">{msg.sender_name}</div>
                    )}
                    <div>{msg.content}</div>
                    {msg.file_url && (
                      <div className="mt-2">
                        <a 
                          href={msg.file_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-300 underline"
                        >
                          📎 {msg.file_name || 'Download'}
                        </a>
                      </div>
                    )}
                    <div className="text-xs opacity-75 mt-1">
                      {formatTime(msg.timestamp)}
                    </div>
                  </div>
                </div>
              ))
            )}
            
            {/* Typing indicator */}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">
                  <div className="flex items-center gap-1">
                    <Spin size="small" />
                    <span className="text-sm">Typing...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2 items-end">
          <Upload
            fileList={fileList}
            onChange={({ fileList }) => setFileList(fileList)}
            beforeUpload={() => false}
            maxCount={1}
            showUploadList={false}
          >
            <Button icon={<PaperClipOutlined />} type="text" />
          </Upload>
          
          <div className="flex-1">
            {fileList.length > 0 && (
              <div className="mb-2 text-sm text-gray-600">
                📎 {fileList[0].name}
                <Button 
                  type="text" 
                  size="small" 
                  onClick={() => setFileList([])}
                >
                  ×
                </Button>
              </div>
            )}
            <Input
              value={inputMessage}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              disabled={!isConnected || loading}
            />
          </div>
          
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={sendMessage}
            disabled={!isConnected || loading || (!inputMessage.trim() && fileList.length === 0)}
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
}
