import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from sqlite_retriever import SQLiteDocumentRetriever as DocumentRetriever
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

    def __init__(
        self,
        retriever: Optional[DocumentRetriever] = None,
        llm_adapter: Optional[GeminiChatAdapter] = None,
    ):
        self.retriever = retriever or DocumentRetriever()
        self.llm_adapter = llm_adapter or GeminiChatAdapter()

        self.conversations: Dict[str, ConversationHistory] = {}

    def initialize(self, force_rebuild_index: bool = False) -> None:
        logger.info("Initializing RAG chat engine...")
        self.retriever.initialize(force_rebuild=force_rebuild_index)
        logger.info("RAG chat engine initialized")

    def chat(
        self,
        request: RAGChatRequest,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> RAGChatResponse:

        start_time = datetime.now()

        try:
            logger.debug(
                f"Attempting to retrieve documents for query: '{request.query}'"
            )

            if not hasattr(self.retriever, "retrieve_documents"):
                logger.error("Retriever does not have retrieve_documents method!")
                logger.info(f"Retriever type: {type(self.retriever)}")
                logger.info(f"Retriever methods: {dir(self.retriever)}")
                retrieved_docs = []
            else:
                try:
                    retrieved_docs = self.retriever.retrieve_documents(
                        query=request.query,
                        config=request.retrieval_config,
                        user_id=user_id,
                    )
                except Exception as retrieve_err:
                    logger.error(
                        f"Error retrieving documents: {retrieve_err}", exc_info=True
                    )
                    retrieved_docs = []

            logger.debug(
                f"Retrieved {len(retrieved_docs)} documents for user {user_id}"
            )

            total_chunks = self.retriever.get_document_count(user_id=user_id)

            if len(retrieved_docs) == 0:
                logger.warning(f"No documents retrieved for query: '{request.query}'")
                logger.info(f"Retrieval config: {request.retrieval_config}")
                logger.info("Trying fallback: search all documents...")
                fallback_config = RetrievalConfig(top_k=10)
                fallback_docs = self.retriever.retrieve_documents(
                    query="document", config=fallback_config, user_id=user_id
                )
                logger.info(f"Fallback search returned: {len(fallback_docs)} documents")
                # Ensure retrieved_docs is updated with fallback results
                retrieved_docs = fallback_docs

            for i, doc in enumerate(retrieved_docs):
                logger.debug(
                    f"  Doc {i+1}: {doc.topic} (score: {doc.similarity_score:.3f}, content_len: {len(doc.content)})"
                )

            context = self._build_context(retrieved_docs, request.chat_config)

            conversation_history = self._get_conversation_history(conversation_id)

            llm_response = self._generate_response(
                query=request.query,
                context=context,
                conversation_history=conversation_history,
                config=request.chat_config,
            )

            if conversation_id:
                self._update_conversation(conversation_id, request.query, llm_response)

            response = RAGChatResponse(
                answer=llm_response,
                context=context,
                conversation_id=conversation_id,
                timestamp=start_time.isoformat(),
                processing_time=(datetime.now() - start_time).total_seconds(),
                retrieved_documents=[doc.model_dump() for doc in retrieved_docs],
                sources=context.sources or [],
            )

            return response

        except Exception as e:
            logger.error(f"Error processing chat request: {e}")

            return RAGChatResponse(
                answer=f"Xin lỗi, đã có lỗi xảy ra khi xử lý câu hỏi của bạn: {str(e)}",
                context=ConversationContext(
                    retrieved_count=0, context_used=False, sources=[]
                ),
                conversation_id=conversation_id,
                timestamp=start_time.isoformat(),
                processing_time=(datetime.now() - start_time).total_seconds(),
                retrieved_documents=[],
                sources=[],
            )

    def _build_context(
        self, retrieved_docs: List, config: ChatConfig
    ) -> ConversationContext:
        if not retrieved_docs:
            return ConversationContext(
                retrieved_count=0, context_used=False, sources=[]
            )

        sources = []
        context_text_parts = []

        for doc in retrieved_docs[: config.max_context_docs]:
            # Ensure content is never None
            raw_content = getattr(doc, "chunk_text", doc.content) or ""
            sources.append(
                {
                    "document_id": doc.document_id,
                    "topic": doc.topic,
                    "category": doc.category,
                    "similarity_score": doc.similarity_score,
                    "chunk_text": (
                        raw_content[:200] + "..."
                        if len(raw_content) > 200
                        else raw_content
                    ),
                }
            )

            chunk_text = raw_content
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
        if not conversation_id or conversation_id not in self.conversations:
            return None

        history = self.conversations[conversation_id]

        recent_messages = history.messages[-6:]
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

        system_prompt = self._build_system_prompt(config)
        user_prompt = self._build_user_prompt(query, context, config)

        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_prompt})

        response = self.llm_adapter.generate_response(messages, config)
        return response

    def _build_system_prompt(self, config: ChatConfig) -> str:

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

        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationHistory(
                conversation_id=conversation_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                messages=[],
            )

        conversation = self.conversations[conversation_id]

        conversation.messages.append(
            {"role": "user", "content": query, "timestamp": datetime.now().isoformat()}
        )

        conversation.messages.append(
            {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        conversation.updated_at = datetime.now().isoformat()

    def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        return self.conversations.get(conversation_id)

    def list_conversations(self, limit: int = 50) -> List[ConversationHistory]:
        conversations = list(self.conversations.values())
        conversations.sort(key=lambda x: x.updated_at, reverse=True)
        return conversations[:limit]

    def delete_conversation(self, conversation_id: str) -> bool:
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
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


_chat_engine = None


def get_chat_engine(retriever: Optional[DocumentRetriever] = None) -> RAGChatEngine:
    global _chat_engine

    if _chat_engine is None:
        _chat_engine = RAGChatEngine(retriever=retriever)

    return _chat_engine


def _add_stats_method():
    def get_stats(self) -> Dict[str, Any]:
        try:
            retriever_stats = (
                self.retriever.get_stats()
                if hasattr(self.retriever, "get_stats")
                else {}
            )

            return {
                "conversations": len(self.conversations),
                "retriever_stats": retriever_stats,
                "engine_initialized": True,
            }
        except Exception as e:
            logger.error(f"Error getting chat engine stats: {e}")
            return {"error": str(e)}

    RAGChatEngine.get_stats = get_stats


_add_stats_method()

__all__ = ["RAGChatEngine", "get_chat_engine"]
