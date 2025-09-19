// Chat types for admin dashboard

// Base chat session interface
export interface ChatSession {
  id: string;
  session_id: string;
  user_name: string;
  user_email?: string;
  company_id: string;
  status: 'pending' | 'active' | 'resolved';
  created_at: string;
  updated_at: string;
  escalated_at?: string;
  assigned_at?: string;
  resolved_at?: string;
  agent_id?: number;
  agent_name?: string;
  last_message?: string;
  message_count?: number;
}

// Chat message interface
export interface ChatMessage {
  id: number;
  session_id: string;
  message_type: 'user' | 'agent' | 'bot';
  content: string;
  timestamp: string;
  sender_name?: string;
  file_url?: string;
  file_name?: string;
  metadata?: any;
}

// Admin dashboard pending session interface (matches admin dashboard API)
export interface PendingSessionData {
  id: number;
  session_id: string;
  user_name: string;
  user_phone: string;
  message: string;
  priority: "LOW" | "MEDIUM" | "HIGH";
  created_at: string;
  waiting_time: string;
}

// Send message request interface
export interface SendMessageRequest {
  session_id: string;
  message: string;
  attachment_ids?: number[];
}

// Send message response interface
export interface SendMessageResponse {
  message: string;
  chat_message: ChatMessage;
}
