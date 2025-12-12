// frontend/src/api/chatAPI.ts

import { API_BASE_URL } from "../contexts/AuthContext";

export interface ChatRequest {
  query: string;
  conversation_id?: string;
  retrieval_config?: {
    top_k?: number;
    similarity_threshold?: number;
  };
  chat_config?: {
    temperature?: number;
    max_tokens?: number;
  };
}

export interface ChatResponse {
  success: boolean;
  data: {
    answer: string;
    context: {
      retrieved_documents: string[];
    };
    processing_time: number;
  };
  error?: string;
}

export interface Conversation {
  conversation_id: string;
  created_at: string;
  message_count: number;
  last_message?: string;
}

export const chatAPI = {
  // Gửi message tới chatbot
  async sendMessage(
    query: string,
    conversationId?: string,
    accessToken?: string
  ): Promise<ChatResponse> {
    const url = `${API_BASE_URL}/rag/chat/`;
    
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    // Thêm authorization token nếu có
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }

    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify({
        query,
        conversation_id: conversationId,
        retrieval_config: {
          top_k: 5,
          similarity_threshold: 0.3,
        },
        chat_config: {
          temperature: 0.7,
          max_tokens: 500,
        },
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Lỗi khi gửi tin nhắn");
    }

    return response.json();
  },

  // Lấy lịch sử chat của một conversation
  async getConversationHistory(
    conversationId: string,
    accessToken?: string
  ): Promise<{ messages: any[] }> {
    const url = `${API_BASE_URL}/rag/conversations/${conversationId}/`;
    
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }

    const response = await fetch(url, {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      return { messages: [] };
    }

    return response.json();
  },

  // Lấy danh sách conversations
  async listConversations(accessToken?: string): Promise<Conversation[]> {
    const url = `${API_BASE_URL}/rag/conversations/?limit=20`;
    
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };

    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }

    const response = await fetch(url, {
      method: "GET",
      headers,
    });

    if (!response.ok) {
      return [];
    }

    const data = await response.json();
    return data.data || [];
  },
};