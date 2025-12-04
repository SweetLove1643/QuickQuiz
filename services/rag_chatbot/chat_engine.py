import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from mongodb_retriever import MongoDBDocumentRetriever as DocumentRetriever
from llm_adapter import GeminiChatAdapter
from schemas import (
    RAGChatRequest,
    RAGChatResponse,
    ConversationContext,
    RetrievalConfig,
    ChatConfig,
    ConversationHistory,
)

logger = logging.getLogger(__name__)


class RAGChatEngine:
    """RAG-based chat engine kết hợp document retrieval và Gemini LLM."""

    def __init__(
        self,
        retriever: Optional[DocumentRetriever] = None,
        llm_adapter: Optional[GeminiChatAdapter] = None,
    ):
        """
        Initialize RAG chat engine.

        Args:
            retriever: Document retriever instance
            llm_adapter: LLM adapter for chat generation
        """
        self.retriever = retriever or DocumentRetriever()
        self.llm_adapter = llm_adapter or GeminiChatAdapter()

        # Conversation storage (in-memory, có thể migrate to DB)
        self.conversations: Dict[str, ConversationHistory] = {}

    def initialize(self, force_rebuild_index: bool = False) -> None:
        """Initialize all components."""
        logger.info("Initializing RAG chat engine...")
        self.retriever.initialize(force_rebuild=force_rebuild_index)
        logger.info("RAG chat engine initialized")

    def chat(
        self, request: RAGChatRequest, conversation_id: Optional[str] = None
    ) -> RAGChatResponse:
        """
        Process chat request sử dụng RAG approach.

        Args:
            request: Chat request với query và configs
            conversation_id: Optional conversation ID for context

        Returns:
            Chat response with answer và context
        """
        start_time = datetime.now()

        try:
            # Debug log
            logger.info(f"=== CHAT ENGINE DEBUG ===")
            logger.info(f"Query: '{request.query}'")
            logger.info(f"Conversation ID: {conversation_id}")
            logger.info(f"Retrieval config: {request.retrieval_config}")

            # 1. Retrieve relevant documents
            retrieved_docs = self.retriever.retrieve_documents(
                query=request.query, config=request.retrieval_config
            )

            logger.info(f"Retrieved {len(retrieved_docs)} documents")
            for i, doc in enumerate(retrieved_docs):
                logger.info(
                    f"  Doc {i+1}: {doc.topic} (score: {doc.similarity_score:.3f})"
                )

            # 2. Build context từ retrieved documents
            context = self._build_context(retrieved_docs, request.chat_config)

            # 3. Get conversation history if available
            conversation_history = self._get_conversation_history(conversation_id)

            # 4. Generate response sử dụng LLM
            llm_response = self._generate_response(
                query=request.query,
                context=context,
                conversation_history=conversation_history,
                config=request.chat_config,
            )

            # 5. Store conversation
            if conversation_id:
                self._update_conversation(conversation_id, request.query, llm_response)

            # 6. Build response
            response = RAGChatResponse(
                answer=llm_response,
                context=context,
                conversation_id=conversation_id,
                timestamp=start_time.isoformat(),
                processing_time=(datetime.now() - start_time).total_seconds(),
                retrieved_documents=[doc.model_dump() for doc in retrieved_docs],
            )

            logger.info(f"Chat processed in {response.processing_time:.2f}s")
            return response

        except Exception as e:
            logger.error(f"Error processing chat request: {e}")

            # Return error response
            return RAGChatResponse(
                answer=f"Xin lỗi, đã có lỗi xảy ra khi xử lý câu hỏi của bạn: {str(e)}",
                context=ConversationContext(
                    retrieved_count=0, context_used=False, sources=[]
                ),
                conversation_id=conversation_id,
                timestamp=start_time.isoformat(),
                processing_time=(datetime.now() - start_time).total_seconds(),
                retrieved_documents=[],
            )

    def _build_context(
        self, retrieved_docs: List, config: ChatConfig
    ) -> ConversationContext:
        """Build context object từ retrieved documents."""
        if not retrieved_docs:
            return ConversationContext(
                retrieved_count=0, context_used=False, sources=[]
            )

        # Collect sources
        sources = []
        context_text_parts = []

        for doc in retrieved_docs[: config.max_context_docs]:
            # Add to sources
            sources.append(
                {
                    "document_id": doc.document_id,
                    "topic": doc.topic,
                    "category": doc.category,
                    "similarity_score": doc.similarity_score,
                    "chunk_text": (
                        getattr(doc, "chunk_text", doc.content or "")[:200] + "..."
                        if len(getattr(doc, "chunk_text", doc.content or "")) > 200
                        else getattr(doc, "chunk_text", doc.content or "")
                    ),
                }
            )

            # Add to context text
            chunk_text = getattr(doc, "chunk_text", doc.content)
            context_text_parts.append(f"[{doc.topic}] {chunk_text}")

        return ConversationContext(
            retrieved_count=len(retrieved_docs),
            context_used=len(sources) > 0,
            sources=sources,
            context_text=(
                "\n\n".join(context_text_parts) if context_text_parts else None
            ),
        )

    def _get_conversation_history(
        self, conversation_id: Optional[str]
    ) -> Optional[List[Dict[str, str]]]:
        """Get conversation history for context."""
        if not conversation_id or conversation_id not in self.conversations:
            return None

        history = self.conversations[conversation_id]

        # Return recent messages for context (limit to avoid token overflow)
        recent_messages = history.messages[-6:]  # Last 6 messages (3 exchanges)

        formatted_history = []
        for msg in recent_messages:
            formatted_history.append({"role": msg["role"], "content": msg["content"]})

        return formatted_history

    def _generate_response(
        self,
        query: str,
        context: ConversationContext,
        conversation_history: Optional[List[Dict[str, str]]],
        config: ChatConfig,
    ) -> str:
        """Generate response sử dụng Gemini LLM."""

        # Build prompt
        system_prompt = self._build_system_prompt(config)
        user_prompt = self._build_user_prompt(query, context, config)

        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user query
        messages.append({"role": "user", "content": user_prompt})

        # Generate response
        response = self.llm_adapter.generate_response(messages, config)
        return response

    def _build_system_prompt(self, config: ChatConfig) -> str:
        """Build system prompt cho Gemini."""

        base_prompt = """Bạn là một trợ lý AI thông minh chuyên trả lời câu hỏi dựa trên các tài liệu và tóm tắt được cung cấp.

NHIỆM VỤ:
- Trả lời câu hỏi của người dùng dựa trên thông tin từ các tài liệu được truy xuất
- Đưa ra câu trả lời chính xác, hữu ích và dễ hiểu
- Sử dụng tiếng Việt một cách tự nhiên và thân thiện
- Trích dẫn thông tin từ các nguồn tài liệu khi có thể

QUY TẮC:
1. Ưu tiên sử dụng thông tin từ các tài liệu được cung cấp
2. Nếu không có thông tin liên quan, hãy thành thật nói rằng bạn không tìm thấy thông tin phù hợp
3. Không tạo ra thông tin không có trong tài liệu
4. Trình bày câu trả lời có cấu trúc, dễ đọc
5. Sử dụng bullet points hoặc danh sách khi phù hợp"""

        if config.include_sources:
            base_prompt += """
6. Luôn đề cập đến nguồn thông tin khi trả lời (ví dụ: "Theo tài liệu về Python...")"""

        if config.response_style:
            base_prompt += f"""
7. Phong cách trả lời: {config.response_style}"""

        return base_prompt

    def _build_user_prompt(
        self, query: str, context: ConversationContext, config: ChatConfig
    ) -> str:
        """Build user prompt với context và query."""

        if not context.context_used or not context.context_text:
            return f"""Câu hỏi: {query}

Lưu ý: Tôi không tìm thấy tài liệu nào liên quan đến câu hỏi này trong cơ sở dữ liệu."""

        prompt_parts = [
            "=== TÀI LIỆU THAM KHẢO ===",
            context.context_text,
            "",
            "=== CÂU HỎI ===",
            query,
        ]

        if config.include_sources:
            prompt_parts.extend(
                [
                    "",
                    "Hãy trả lời dựa trên các tài liệu trên và đề cập đến nguồn thông tin.",
                ]
            )
        else:
            prompt_parts.extend(["", "Hãy trả lời dựa trên các tài liệu trên."])

        return "\n".join(prompt_parts)

    def _update_conversation(
        self, conversation_id: str, query: str, response: str
    ) -> None:
        """Update conversation history."""

        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationHistory(
                conversation_id=conversation_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                messages=[],
            )

        conversation = self.conversations[conversation_id]

        # Add user message
        conversation.messages.append(
            {"role": "user", "content": query, "timestamp": datetime.now().isoformat()}
        )

        # Add assistant response
        conversation.messages.append(
            {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        conversation.updated_at = datetime.now().isoformat()

    def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Get conversation by ID."""
        return self.conversations.get(conversation_id)

    def list_conversations(self, limit: int = 50) -> List[ConversationHistory]:
        """List recent conversations."""
        conversations = list(self.conversations.values())
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return conversations[:limit]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation by ID."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get chat engine statistics."""
        retriever_stats = self.retriever.get_stats()

        return {
            "retriever": retriever_stats,
            "conversations": {
                "total_conversations": len(self.conversations),
                "total_messages": sum(
                    len(conv.messages) for conv in self.conversations.values()
                ),
            },
            "llm_adapter": {
                "model": getattr(self.llm_adapter, "current_model", "unknown"),
                "status": "ready",
            },
        }


# Global chat engine instance (singleton pattern)
_chat_engine = None


def get_chat_engine(retriever: Optional[DocumentRetriever] = None) -> RAGChatEngine:
    """
    Get global chat engine instance.

    Args:
        retriever: Optional document retriever

    Returns:
        RAGChatEngine instance
    """
    global _chat_engine

    if _chat_engine is None:
        _chat_engine = RAGChatEngine(retriever=retriever)

    return _chat_engine


__all__ = ["RAGChatEngine", "get_chat_engine"]
