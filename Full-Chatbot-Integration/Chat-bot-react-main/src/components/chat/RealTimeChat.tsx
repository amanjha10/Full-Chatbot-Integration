import React, { useState, useEffect, useRef } from "react";
import { Button, Input, Upload, message, Spin } from "antd";
import { SendOutlined, PaperClipOutlined } from "@ant-design/icons";
import type { UploadFile } from "antd/es/upload/interface";

interface ChatMessage {
  id: string;
  type: "user" | "agent" | "system";
  content: string;
  timestamp: string;
  sender_name?: string;
  file_url?: string;
  file_name?: string;
}

interface RealTimeChatProps {
  sessionId: string;
  companyId: string;
  userType: "agent" | "user";
  userName?: string;
  onClose?: () => void;
}

export default function RealTimeChat({
  sessionId,
  companyId,
  userType,
  userName,
  onClose,
}: RealTimeChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState("");
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
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch chat history
  const fetchChatHistory = React.useCallback(async () => {
    if (userType !== "agent") return;

    try {
      setLoadingHistory(true);
      const token = localStorage.getItem("access_token");

      const response = await fetch(
        `http://127.0.0.1:8001/api/human-handoff/agent/sessions/${sessionId}/messages/`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        const chatMessages: ChatMessage[] = data.messages.map(
          (msg: {
            id: number;
            message_type: string;
            content: string;
            timestamp: string;
            file_url?: string;
            file_name?: string;
            attachments?: any[];
          }) => ({
            id: msg.id.toString(),
            type:
              msg.message_type === "user"
                ? "user"
                : msg.message_type === "bot"
                ? "agent"
                : "system",
            content: msg.content,
            timestamp: msg.timestamp,
            sender_name:
              msg.message_type === "user"
                ? data.session.user_profile?.name || "User"
                : "Bot",
            file_url: msg.file_url,
            file_name: msg.file_name,
          })
        );

        setMessages(chatMessages);
        console.log("Chat history loaded:", chatMessages.length, "messages");
      } else {
        console.error("Failed to fetch chat history:", response.status);
        message.error("Failed to load chat history");
      }
    } catch (error) {
      console.error("Error fetching chat history:", error);
      message.error("Error loading chat history");
    } finally {
      setLoadingHistory(false);
    }
  }, [sessionId, userType]);

  // Load chat history when component mounts
  useEffect(() => {
    fetchChatHistory();
  }, [fetchChatHistory]);

  // Initialize WebSocket connection (optional - only works for escalated sessions)
  useEffect(() => {
    const wsUrl = `ws://localhost:8000/ws/chat/${companyId}/${sessionId}/`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);

      // Request file list to sync existing files
      ws.send(JSON.stringify({
        type: 'request_file_list',
        session_id: sessionId,
        company_id: companyId
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);


        switch (data.type) {
          case "chat_message":
            // Add deduplication for chat messages
            setMessages((prev) => {
              const messageId = data.message_id || Date.now().toString();
              const isDuplicate = prev.some(msg =>
                msg.id === messageId ||
                (msg.content === data.message &&
                 msg.type === data.sender_type &&
                 Math.abs(new Date(msg.timestamp).getTime() - new Date(data.timestamp || Date.now()).getTime()) < 5000)
              );

              if (isDuplicate) {
                return prev;
              }

              return [
                ...prev,
                {
                  id: messageId,
                  type: data.sender_type,
                  content: data.message,
                  timestamp: data.timestamp || new Date().toISOString(),
                  sender_name: data.sender_name,
                  file_url: data.file_url,
                  file_name: data.file_name,
                },
              ];
            });
            break;

          case "typing_indicator":
            if (data.sender_type !== userType) {
              setIsTyping(data.is_typing);
            }
            break;

          case "system_message":
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now().toString(),
                type: "system",
                content: data.message,
                timestamp: data.timestamp,
              },
            ]);
            break;

          case "connection_established":
            break;

          case "file_shared":
            // Validate file data before adding
            if (data.id && data.name && data.url) {
              // Check for duplicate file messages
              setMessages((prev) => {
                const isDuplicate = prev.some(msg =>
                  msg.id === data.id?.toString() ||
                  (msg.file_url === data.url && msg.file_name === data.name)
                );

                if (isDuplicate) {
                  return prev;
                }

                return [
                  ...prev,
                  {
                    id: data.id.toString(),
                    type: data.uploader === "user" ? "user" : "agent",
                    content: `📎 Shared file: ${data.name}`,
                    timestamp: data.created_at || new Date().toISOString(),
                    sender_name: data.uploader === "user" ? "User" : "Agent",
                    file_url: data.url,
                    file_name: data.name,
                  },
                ];
              });
            } else {
              console.warn("Invalid file_shared data:", data);
            }
            break;

          case "file_list":
            console.log("File list received:", data.files);
            // File list is now handled by the API response, no need to create separate messages
            // The chat history API will include file attachments directly in messages
            break;

          case "error":
            message.error(data.message);
            break;

          default:
            console.log("Unknown WebSocket message type:", data.type);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };
    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = () => {
      // Connection failures are normal when session isn't escalated
      // No need to log or show errors for this
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
      if (userType === "agent") {
        const token = localStorage.getItem("access_token");

        // Handle file upload if present
        if (fileList.length > 0) {
          const formData = new FormData();
          formData.append("file", fileList[0].originFileObj as File);
          formData.append("session_id", sessionId);

          // Add required fields for new unified API
          formData.append("company_id", companyId);
          formData.append("uploader", "agent");

          const uploadResponse = await fetch(
            "http://127.0.0.1:8001/api/chat/upload/",
            {
              method: "POST",
              headers: {
                Authorization: `Bearer ${token}`,
              },
              body: formData,
            }
          );

          if (!uploadResponse.ok) {
            throw new Error("Failed to upload file");
          }
          // File upload successful - file_shared event will handle display
        }

        // Only send message if there's actual text content
        let response = null;
        if (inputMessage.trim()) {
          response = await fetch(
            "http://127.0.0.1:8001/api/human-handoff/agent/send-message/",
            {
              method: "POST",
              headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                session_id: sessionId,
                message: inputMessage.trim(),
              }),
            }
          );
        }

        if (response && response.ok) {
          // Don't add to local state - WebSocket will handle message display

          // Also send via WebSocket for real-time updates to user
          // Note: Don't include file info here since file upload already triggered file_shared event
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(
              JSON.stringify({
                type: "chat_message",
                message: inputMessage.trim(),
                sender_type: "agent",
                sender_name: userName || "Agent",
                // file_url and file_name removed to prevent duplicate file messages
              })
            );
          }
        } else if (response && !response.ok) {
          const errorData = await response.text();
          console.error("Agent API Error Response:", errorData);
          throw new Error(
            `Failed to send message via API: ${response.status} - ${errorData}`
          );
        }
        // If no response (file-only upload), that's fine - file_shared event will handle it
      } else {
        // For users, use direct WebSocket
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          // Connection not available - this is normal for non-escalated sessions
          // Fall back to HTTP API instead of showing error
          console.log("WebSocket not available, using HTTP API");
          return;
        }

        // Handle file upload if present
        if (fileList.length > 0) {
          const formData = new FormData();
          formData.append("file", fileList[0].originFileObj as File);
          formData.append("session_id", sessionId);

          // Use the new unified upload endpoint
          const uploadEndpoint = "http://127.0.0.1:8001/api/chat/upload/";

          // Add required fields for new unified API
          formData.append("company_id", companyId);
          formData.append("uploader", "user");

          const headers: Record<string, string> = {};

          const response = await fetch(uploadEndpoint, {
            method: "POST",
            headers,
            body: formData,
          });

          if (!response.ok) {
            throw new Error("File upload failed");
          }
          // File upload successful - file_shared event will handle display
        }

        // Send message via WebSocket
        // Note: Don't include file info here since file upload already triggered file_shared event
        wsRef.current.send(
          JSON.stringify({
            type: "chat_message",
            message: inputMessage.trim(),
            sender_type: userType,
            sender_name: userName || "User",
            session_id: sessionId,
            // file_url and file_name removed to prevent duplicate file messages
          })
        );
      }

      // Clear input
      setInputMessage("");
      setFileList([]);
    } catch (err) {
      console.error("Error sending message:", err);
      message.error("Failed to send message");
    } finally {
      setLoading(false);
    }
  };

  // Handle typing indicator
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputMessage(e.target.value);

    // Send typing indicator
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "typing_indicator",
          is_typing: true,
          sender_type: userType,
        })
      );

      // Clear previous timeout
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }

      // Set timeout to stop typing indicator
      typingTimeoutRef.current = setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              type: "typing_indicator",
              is_typing: false,
              sender_type: userType,
            })
          );
        }
      }, 1000);
    }
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b bg-gray-50">
        <div className="flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${
              isConnected ? "bg-green-500" : "bg-red-500"
            }`}
          ></div>
          <span className="font-medium">
            {userType === "agent" ? `Chat with User` : "Support Chat"}
          </span>
        </div>
        {onClose && (
          <Button type="text" onClick={onClose}>
            ×
          </Button>
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
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.type === userType ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      msg.type === "system"
                        ? "bg-gray-100 text-gray-600 text-center text-sm"
                        : msg.type === userType
                        ? "bg-blue-500 text-white"
                        : "bg-gray-200 text-gray-800"
                    }`}
                  >
                    {msg.type !== "system" && msg.sender_name && (
                      <div className="text-xs opacity-75 mb-1">
                        {msg.sender_name}
                      </div>
                    )}
                    <div>{msg.content}</div>
                    {msg.file_url && (
                      <div className="mt-2">
                        {/* Check if file is an image */}
                        {/\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(msg.file_name || '') ? (
                          <div className="file-image-preview bg-gray-50 rounded-lg p-3 max-w-xs">
                            <img
                              src={msg.file_url}
                              alt={msg.file_name || 'Image'}
                              className="max-w-full max-h-48 rounded-lg cursor-pointer border shadow-sm hover:shadow-md transition-shadow"
                              onError={(e) => {
                                // Fallback for broken images
                                e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlPC90ZXh0Pjwvc3ZnPg==';
                              }}
                              onClick={() => {
                                const link = document.createElement('a');
                                link.href = msg.file_url || '#';
                                link.download = msg.file_name || 'image';
                                link.style.display = 'none';
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                              }}
                            />
                            <div className="flex items-center justify-between mt-2">
                              <div className="text-xs text-gray-600 truncate flex-1">
                                📷 {msg.file_name || 'Image'}
                              </div>
                              <button
                                onClick={() => {
                                  const link = document.createElement('a');
                                  link.href = msg.file_url || '#';
                                  link.download = msg.file_name || 'image';
                                  link.style.display = 'none';
                                  document.body.appendChild(link);
                                  link.click();
                                  document.body.removeChild(link);
                                }}
                                className="ml-2 px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                              >
                                Download
                              </button>
                            </div>
                          </div>
                        ) : (
                          <a
                            href={msg.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-300 underline"
                          >
                            📎 {msg.file_name || "Download"}
                          </a>
                        )}
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
              onKeyDown={handleKeyPress}
              placeholder="Type a message..."
              disabled={!isConnected || loading}
            />
          </div>

          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={sendMessage}
            disabled={
              !isConnected ||
              loading ||
              (!inputMessage.trim() && fileList.length === 0)
            }
            loading={loading}
          />
        </div>
      </div>
    </div>
  );
}
