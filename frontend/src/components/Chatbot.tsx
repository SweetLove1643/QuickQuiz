import { useState, useRef, useEffect } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card } from "./ui/card";
import {
  Send,
  Loader2,
  MessageCircle,
  Book,
  Zap,
  Copy,
  Check,
} from "lucide-react";
import { chatbotAPI } from "../api/quizAPI";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: Array<{
    content: string;
    topic?: string;
    similarity_score?: number;
  }>;
}

interface ChatbotProps {
  documentId?: string;
  documentName?: string;
}

export function Chatbot({ documentId, documentName }: ChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      type: "assistant",
      content: `Xin chào! 👋 Tôi là chatbot RAG của QuickQuiz. Tôi có thể giúp bạn:
      
• Trả lời các câu hỏi về tài liệu của bạn
• Giải thích các khái niệm trong bài học
• Cung cấp ví dụ liên quan
• Hỗ trợ ôn tập

${
  documentName
    ? `📄 Đang làm việc với: ${documentName}`
    : "Hãy upload một tài liệu để bắt đầu!"
}`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId] = useState(() => `conv-${Date.now()}`);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      type: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await chatbotAPI.sendMessage({
        query: input,
        conversation_id: conversationId,
        document_id: documentId,
        retrieval_config: {
          top_k: 5,
          similarity_threshold: 0.3,
        },
        chat_config: {
          temperature: 0.7,
          max_tokens: 500,
        },
      });

      const assistantMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        type: "assistant",
        content: response.answer,
        timestamp: new Date(),
        sources: response.context.retrieved_documents.map((doc) => ({
          content: doc.content || String(doc),
          similarity_score: doc.similarity_score,
        })),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);

      const errorMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        type: "assistant",
        content:
          error instanceof Error
            ? error.message
            : "Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi của bạn. Vui lòng thử lại sau.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const suggestedQuestions = [
    "Khái niệm chính là gì?",
    "Có thể giải thích chi tiết hơn không?",
    "Ví dụ cụ thể là gì?",
  ];

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg border border-slate-200">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <MessageCircle className="size-5 text-blue-600" />
        <div className="flex-1">
          <h2 className="text-lg font-semibold text-slate-900">RAG Chatbot</h2>
          {documentName && (
            <p className="text-sm text-slate-600">
              Đang tương tác với: {documentName}
            </p>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.type === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[70%] rounded-lg px-4 py-3 ${
                message.type === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-slate-200 text-slate-900"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>

              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-300 space-y-2">
                  <p className="text-xs font-semibold opacity-70">
                    📚 Nguồn tham khảo:
                  </p>
                  {message.sources.slice(0, 3).map((source, idx) => (
                    <div key={idx} className="bg-slate-100 rounded p-2 text-xs">
                      <p className="line-clamp-2">{source.content}</p>
                      {source.similarity_score && (
                        <p className="text-xs opacity-60 mt-1">
                          Độ tương đồng:{" "}
                          {(source.similarity_score * 100).toFixed(0)}%
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Copy button for assistant messages */}
              {message.type === "assistant" && (
                <button
                  onClick={() => copyToClipboard(message.content, message.id)}
                  className="mt-2 inline-flex items-center gap-1 px-2 py-1 text-xs rounded hover:bg-slate-200 opacity-70 hover:opacity-100 transition-opacity"
                >
                  {copiedId === message.id ? (
                    <>
                      <Check className="size-3" /> Đã sao chép
                    </>
                  ) : (
                    <>
                      <Copy className="size-3" /> Sao chép
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-lg px-4 py-3 flex items-center gap-2">
              <Loader2 className="size-4 text-blue-600 animate-spin" />
              <span className="text-sm text-slate-600">Đang suy nghĩ...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested questions */}
      {messages.length <= 1 && !isLoading && (
        <div className="px-4 py-3 border-t border-slate-200 bg-white">
          <p className="text-xs font-semibold text-slate-600 mb-2">
            💡 Câu hỏi gợi ý:
          </p>
          <div className="flex gap-2 flex-wrap">
            {suggestedQuestions.map((question, idx) => (
              <button
                key={idx}
                onClick={() => setInput(question)}
                className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-xs rounded-full text-slate-700 transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={handleSendMessage}
        className="flex gap-2 p-4 border-t border-slate-200 bg-white"
      >
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Đặt câu hỏi của bạn..."
          disabled={isLoading || !documentId}
          className="flex-1"
        />
        <Button
          type="submit"
          disabled={isLoading || !input.trim() || !documentId}
          className="px-4"
        >
          {isLoading ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Send className="size-4" />
          )}
        </Button>
      </form>

      {!documentId && (
        <div className="px-4 py-2 bg-yellow-50 border-t border-yellow-200 text-xs text-yellow-700 flex items-center gap-2">
          <Zap className="size-4" />
          Chatbot có thể hoạt động tốt hơn khi bạn chọn một tài liệu cụ thể
        </div>
      )}
    </div>
  );
}
