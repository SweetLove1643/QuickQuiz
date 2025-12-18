import os
import sys
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Query, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from chat_engine import get_chat_engine, RAGChatEngine

from sqlite_retriever import SQLiteDocumentRetriever as DocumentRetriever
from schemas import (
    RAGChatRequest,
    RAGChatResponse,
    RetrievalConfig,
    ChatConfig,
    ConversationHistory,
    ConversationListResponse,
    HealthResponse,
)
from database import (
    init_db,
    log_conversation,
    log_chat_message,
    get_conversation_history,
    quiz_data_access,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Chatbot API",
    description="REST API cho RAG-based chatbot system với document retrieval",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
_chat_engine: Optional[RAGChatEngine] = None
_retriever: Optional[DocumentRetriever] = None


@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        logger.info("✅ RAG Chatbot database initialized")

        templates = quiz_data_access.get_quiz_templates(1)
        logger.info(f"✅ Quiz data access working - found {len(templates)} templates")

        gateway_docs = quiz_data_access.get_gateway_documents(1)
        logger.info(f"✅ Gateway documents accessible: {len(gateway_docs)} found")
        
        logger.info(f"Quiz DB path: {quiz_data_access.quiz_generator_db}")
        logger.info(f"Gateway DB path: {quiz_data_access.gateway_documents_db}")

    except Exception as e:
        logger.error(f"❌ Startup initialization failed: {e}")


async def _process_chat_request(
    request: RAGChatRequest,
    conversation_id: Optional[str] = None,
    chat_engine: RAGChatEngine = None,
) -> RAGChatResponse:
    try:
        effective_conversation_id = conversation_id or request.conversation_id

        log_query = (
            request.query[:50] + "..." if len(request.query) > 50 else request.query
        )
        logger.info(f"=== CHAT REQUEST DEBUG ===")
        logger.info(f"Query: {log_query}")
        logger.info(f"Conversation ID: {effective_conversation_id}")
        logger.info(f"Retrieval config: top_k={request.retrieval_config.top_k}")
        logger.info(f"Chat config: temperature={request.chat_config.temperature}")

        if effective_conversation_id:
            logger.info(
                f"Processing chat in conversation {effective_conversation_id[:8]}: {log_query}"
            )
        else:
            logger.info(f"Processing standalone chat: {log_query}")

        quiz_context = []
        try:
            quiz_content = quiz_data_access.search_quiz_content(request.query, 3)
            if quiz_content:
                quiz_context = quiz_content
                logger.info(f"Found {len(quiz_content)} relevant quiz contexts")
        except Exception as e:
            logger.warning(f"Could not access quiz context: {e}")

        response = chat_engine.chat(request, effective_conversation_id)

        try:
            retrieved_docs = []
            if hasattr(response.context, 'sources') and response.context.sources:
                retrieved_docs = [
                    {
                        "content": str(source)[:200] + "..." if len(str(source)) > 200 else str(source),
                        "source": "document_retrieval",
                    }
                    for source in response.context.sources[:3]
                ]
            
            await log_chat_message(
                conversation_id=effective_conversation_id or "standalone",
                user_query=request.query,
                assistant_response=response.answer,
                retrieved_documents=retrieved_docs,
            )
        except Exception as e:
            logger.warning(f"Could not log chat message: {e}")

        logger.info(f"=== CHAT RESPONSE DEBUG ===")
        logger.info(f"Retrieved docs: {response.context.retrieved_count}")
        logger.info(f"Context used: {response.context.context_used}")
        logger.info(f"Quiz context: {len(quiz_context)} items")
        logger.info(f"Processing time: {response.processing_time:.2f}s")
        logger.info(f"Answer preview: {response.answer[:100]}...")

        return response

    except Exception as e:
        error_context = (
            f"conversation {conversation_id[:8]}"
            if conversation_id
            else "standalone chat"
        )
        logger.error(f"Chat processing error in {error_context}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


def get_retriever_instance() -> DocumentRetriever:
    global _retriever
    if _retriever is None:
        _retriever = DocumentRetriever()
        _retriever.initialize()
    return _retriever


def get_chat_engine_instance() -> RAGChatEngine:
    global _chat_engine
    if _chat_engine is None:
        retriever = get_retriever_instance()
        _chat_engine = get_chat_engine(retriever=retriever)
        _chat_engine.initialize()
    return _chat_engine


@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        retriever = get_retriever_instance()
        chat_engine = get_chat_engine_instance()

        quiz_templates = quiz_data_access.get_quiz_templates(1)
        quiz_access_ok = (
            len(quiz_templates) >= 0
        ) 

        stats = chat_engine.get_stats()

        return HealthResponse(
            status="healthy", service="rag_chatbot_service", version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post(
    "/chat",
    response_model=RAGChatResponse,
    summary="Smart Chat Endpoint",
    description="""
          **Unified chat endpoint với smart conversation handling.**
          
          **Behavior:**
          - **Nếu có conversation_id**: Tiếp tục conversation existing (như /conversations/{id}/chat)
          - **Nếu không có conversation_id**: Tạo conversation mới (new chat)
          
          **Features:**
          - Auto-detect conversation mode
          - Retrieve documents từ knowledge base  
          - Generate response với Gemini LLM
          - Flexible conversation management
          
          **Use Cases:**
          1. **New Chat**: Không truyền conversation_id → Tạo mới
          2. **Continue Chat**: Truyền conversation_id → Tiếp tục existing
          
          **Example - New Chat:**
          ```json
          {
            "query": "Python là gì?",
            "conversation_id": null
          }
          ```
          
          **Example - Continue Chat:**
          ```json
          {
            "query": "Giải thích thêm về syntax",
            "conversation_id": "447c35cc-a5f1-4a76-9306-9480ce9a574d"
          }
          ```
          """,
)
async def chat_with_rag(
    request: RAGChatRequest,
    chat_engine: RAGChatEngine = Depends(get_chat_engine_instance),
):

    if not request.conversation_id:
        request.conversation_id = str(uuid.uuid4())
        logger.info(
            f"New Chat - Auto-generated conversation ID: {request.conversation_id}"
        )
    else:
        logger.info(
            f"Continue Chat - Using existing conversation ID: {request.conversation_id[:8]}..."
        )

    return await _process_chat_request(
        request=request,
        conversation_id=request.conversation_id,
        chat_engine=chat_engine,
    )


@app.post(
    "/chat/quick",
    summary="Quick Anonymous Chat",
    description="""
          **Quick chat cho anonymous users.**
          
          Features:  
          - Không cần authentication
          - Không lưu conversation history
          - Simplified parameters via URL query
          - Perfect cho testing và demo
          
          **Use Cases:**
          - Users chưa đăng nhập
          - One-time queries  
          - API testing
          - Public demos
          
          **Example:**
          `POST /chat/quick?query=Python là gì&top_k=5&temperature=0.7`
          """,
)
async def quick_chat(
    query: str = Query(
        ...,
        description="Câu hỏi của user",
        min_length=1,
        max_length=2000,
        example="Python là gì?",
    ),
    top_k: int = Query(
        default=5, description="Số lượng documents tìm kiếm", ge=1, le=20
    ),
    temperature: float = Query(
        default=0.7, description="Độ sáng tạo của LLM (0.0-2.0)", ge=0.0, le=2.0
    ),
    chat_engine: RAGChatEngine = Depends(get_chat_engine_instance),
):
    try:
        request = RAGChatRequest(
            query=query,
            retrieval_config=RetrievalConfig(top_k=top_k),
            chat_config=ChatConfig(temperature=temperature),
            conversation_id=None, 
        )

        response = await _process_chat_request(
            request=request,
            conversation_id=None, 
            chat_engine=chat_engine,
        )

        return {
            "answer": response.answer,
            "sources_count": response.context.retrieved_count,
            "processing_time": response.processing_time,
            "sources": response.context.sources[:3] if response.context.sources else [],
            "conversation_id": None,
        }

    except Exception as e:
        logger.error(f"Quick chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Quick chat failed: {str(e)}")


@app.post(
    "/conversations/{conversation_id}/chat",
    response_model=RAGChatResponse,
    summary="Continue Conversation (Legacy)",
    description="""
          **[LEGACY] Tiếp tục chat trong existing conversation.**
          
          **Note**: Endpoint này giờ có thể được thay thế bằng `/chat` với conversation_id trong body.
          
          **Differences với /chat:**
          - **URL Path**: Conversation ID trong URL thay vì request body
          - **Override**: Luôn override conversation_id từ URL
          - **Legacy Support**: Maintain backward compatibility
          
          **Recommended**: Sử dụng `/chat` endpoint với conversation_id trong body.
          
          **Example:**
          ```
          POST /conversations/447c35cc-a5f1-4a76-9306-9480ce9a574d/chat
          ```
          """,
)
async def chat_in_conversation(
    conversation_id: str = Path(
        ...,
        description="ID của conversation cần tiếp tục",
        example="447c35cc-a5f1-4a76-9306-9480ce9a574d",
    ),
    request: RAGChatRequest = ...,
    chat_engine: RAGChatEngine = Depends(get_chat_engine_instance),
):
    request.conversation_id = conversation_id

    logger.info(
        f"Legacy endpoint - Using conversation ID from URL: {conversation_id[:8]}..."
    )

    return await _process_chat_request(
        request=request, conversation_id=conversation_id, chat_engine=chat_engine
    )


@app.get("/conversations/{conversation_id}", response_model=ConversationHistory)
async def get_conversation(
    conversation_id: str, chat_engine: RAGChatEngine = Depends(get_chat_engine_instance)
):
    try:
        conversation = chat_engine.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = Query(
        default=20, description="Maximum conversations to return", ge=1, le=100
    ),
    chat_engine: RAGChatEngine = Depends(get_chat_engine_instance),
):
    try:
        conversations = chat_engine.list_conversations(limit=limit)

        return ConversationListResponse(
            conversations=conversations,
            total=len(conversations),
            has_more=False,
        )

    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str, chat_engine: RAGChatEngine = Depends(get_chat_engine_instance)
):
    try:
        success = chat_engine.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search/documents")
async def search_documents(
    query: str = Query(..., description="Search query", min_length=1),
    top_k: int = Query(default=10, description="Number of results", ge=1, le=50),
    threshold: float = Query(
        default=0.3, description="Similarity threshold", ge=0.0, le=1.0
    ),
    topic: Optional[str] = Query(default=None, description="Filter by topic"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    retriever: DocumentRetriever = Depends(get_retriever_instance),
):
    try:
        config = RetrievalConfig(
            top_k=top_k, similarity_threshold=threshold, topic_filter=topic
        )

        results = retriever.retrieve_documents(query, config)

        if category:
            results = [r for r in results if r.category.lower() == category.lower()]

        return {
            "query": query,
            "results_count": len(results),
            "documents": [doc.model_dump() for doc in results],
            "search_params": {
                "top_k": top_k,
                "threshold": threshold,
                "topic_filter": topic,
                "category_filter": category,
            },
        }

    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{document_id}")
async def get_document_by_id(
    document_id: str, retriever: DocumentRetriever = Depends(get_retriever_instance)
):
    try:
        document = retriever.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metadata/topics")
async def list_topics(retriever: DocumentRetriever = Depends(get_retriever_instance)):
    try:
        topics = retriever.list_all_topics()
        return {"topics": topics, "count": len(topics)}

    except Exception as e:
        logger.error(f"List topics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metadata/categories")
async def list_categories(
    retriever: DocumentRetriever = Depends(get_retriever_instance),
):
    try:
        categories = retriever.list_all_categories()
        return {"categories": categories, "count": len(categories)}

    except Exception as e:
        logger.error(f"List categories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metadata/filters")
async def get_filter_options(
    retriever: DocumentRetriever = Depends(get_retriever_instance),
):
    try:
        topics = retriever.list_all_topics()
        categories = retriever.list_all_categories()

        return {
            "topics": topics,
            "categories": categories,
            "total_topics": len(topics),
            "total_categories": len(categories),
        }

    except Exception as e:
        logger.error(f"Get filter options error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_system_stats(
    chat_engine: RAGChatEngine = Depends(get_chat_engine_instance),
):
    try:
        stats = chat_engine.get_stats()

        return {
            "timestamp": datetime.now().isoformat(),
            "retriever_stats": stats["retriever"],
            "conversation_stats": stats["conversations"],
            "llm_stats": stats["llm_adapter"],
            "api_info": {
                "service": "rag-chatbot-api",
                "version": "1.0.0",
                "endpoints": len(app.routes),
            },
        }

    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/rebuild-index")
async def rebuild_search_index(
    retriever: DocumentRetriever = Depends(get_retriever_instance),
):
    try:
        logger.info("Rebuilding search index...")
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, retriever.rebuild_index)
        
        stats = retriever.get_stats()
        logger.info(f"Rebuild complete. Stats: {stats}")
        
        test_results = retriever.search_documents("test", RetrievalConfig(top_k=1))
        logger.info(f"Test search after rebuild: {len(test_results)} documents found")

        return {
            "message": "Search index rebuilt successfully",
            "timestamp": datetime.now().isoformat(),
            "stats": stats,
            "test_search_results": len(test_results),
        }

    except Exception as e:
        logger.error(f"Rebuild index error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/clear-cache")
async def clear_system_cache(
    retriever: DocumentRetriever = Depends(get_retriever_instance),
):
    try:
        logger.info("Clearing system cache...")
        retriever.clear_cache()

        return {
            "message": "System cache cleared successfully",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Clear cache error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal error occurred while processing the request",
            "timestamp": datetime.now().isoformat(),
        },
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(description="RAG Chatbot API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=8006, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"][
        "fmt"
    ] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"

    print(f"Starting RAG Chatbot API server...")
    print(f"Server: http://{args.host}:{args.port}")
    print(f"Docs: http://{args.host}:{args.port}/docs")
    print(f"Auto-reload: {args.reload}")

    uvicorn.run(
        "api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        log_config=log_config,
    )


if __name__ == "__main__":
    main()
