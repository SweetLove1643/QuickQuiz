# RAG Chatbot Package

RAG (Retrieval-Augmented Generation) chatbot system cho Q&A từ document summaries sử dụng vector similarity search và Gemini AI.

## 🎯 Tính năng chính

- **Document Retrieval**: Vector search sử dụng FAISS và sentence-transformers
- **Conversational AI**: Gemini API integration với conversation context
- **Local Embeddings**: Offline text embedding với all-MiniLM-L6-v2
- **REST API**: FastAPI server với comprehensive endpoints
- **Command-line Interface**: Interactive CLI cho development/testing
- **Document Management**: Chunking, metadata, filtering capabilities
- **Performance Optimization**: Index caching, multi-model fallback

## 📦 Cấu trúc Package

```
rag_chatbot/
├── __init__.py                 # Package initialization
├── requirements.txt            # Dependencies
├── schemas.py                  # Pydantic data models
├── embeddings.py               # Text embedding service
├── vector_store.py            # FAISS vector database
├── retriever.py               # Document retrieval system
├── llm_adapter.py             # Gemini LLM integration
├── chat_engine.py             # Core RAG chat engine
├── main.py                    # Command-line interface
├── api.py                     # FastAPI REST server
├── demo.py                    # Example usage và demos
├── README.md                  # Documentation
├── data/
│   └── mock_summaries.json    # Sample document data
└── cache/                     # FAISS index cache (auto-created)
```

## 🛠️ Cài đặt

### 1. Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Tạo `.env` file ở project root:

```env
# Gemini API Configuration
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Development mode (sử dụng canned responses)
USE_CANNED_LLM=false
```

### 3. Khởi tạo System

```bash
# Initialize và build search index
python main.py --init

# Force rebuild index từ source data
python main.py --rebuild
```

## 🚀 Sử dụng

### Command-line Interface

```bash
# Interactive chat mode
python main.py --interactive

# Single query
python main.py --query "Python có những đặc điểm gì?"

# Custom data source
python main.py --data /path/to/your/summaries.json
```

### REST API Server

```bash
# Start API server (port 8006)
python api.py

# Custom host/port
python api.py --host localhost --port 8000 --reload
```

### Python Integration

```python
from rag_chatbot import get_chat_engine, RAGChatRequest, ChatConfig

# Initialize
chat_engine = get_chat_engine()
chat_engine.initialize()

# Create request
request = RAGChatRequest(
    query="Giải thích về Python programming language",
    chat_config=ChatConfig(temperature=0.7)
)

# Get response
response = chat_engine.chat(request)
print(response.answer)
```

## 📖 API Endpoints

### Chat Endpoints

```http
POST /chat
Content-Type: application/json

{
  "query": "Python có những ưu điểm gì?",
  "retrieval_config": {
    "top_k": 5,
    "similarity_threshold": 0.3
  },
  "chat_config": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "include_sources": true
  }
}
```

### Quick Chat

```http
POST /chat/quick?query=Python+có+những+ưu+điểm+gì&top_k=3&temperature=0.8
```

### Document Search

```http
GET /search/documents?query=machine+learning&top_k=10&category=AI
```

### Conversation Management

```http
GET /conversations                          # List conversations
POST /conversations/{id}/chat              # Chat in conversation
GET /conversations/{id}                    # Get conversation
DELETE /conversations/{id}                 # Delete conversation
```

### Metadata

```http
GET /metadata/topics                       # List topics
GET /metadata/categories                   # List categories
GET /stats                                # System statistics
```

## 🏗️ Kiến trúc System

### RAG Pipeline

1. **Query Processing**: Nhận user query và config
2. **Document Retrieval**: Vector search trong FAISS index
3. **Context Building**: Aggregate relevant document chunks
4. **LLM Generation**: Gemini API với augmented context
5. **Response Formatting**: Structure output với sources

### Core Components

- **TextEmbedding**: Sentence-transformers cho local embeddings
- **FAISSVectorStore**: Vector database với similarity search
- **DocumentRetriever**: Orchestrate search và ranking
- **RAGChatEngine**: Main conversation logic
- **GeminiChatAdapter**: LLM integration với retry logic

### Data Flow

```
User Query → Embedding → Vector Search → Document Chunks →
Context Building → Gemini LLM → Generated Response
```

## ⚙️ Configuration

### Retrieval Config

```python
RetrievalConfig(
    top_k=5,                    # Number of documents to retrieve
    similarity_threshold=0.3,    # Minimum similarity score
    chunk_size=200,             # Characters per chunk
    chunk_overlap=50,           # Overlap between chunks
    topic_filter="Python",      # Filter by topic
    include_metadata=True       # Include document metadata
)
```

### Chat Config

```python
ChatConfig(
    temperature=0.7,            # LLM creativity (0.0-2.0)
    top_p=0.9,                 # Nucleus sampling
    max_tokens=2048,           # Max response length
    max_context_docs=5,        # Max docs in context
    include_sources=True,      # Include source references
    response_style="helpful"   # Response style preference
)
```

## 📊 Performance Features

### Caching Strategy

- **FAISS Index**: Persistent index cache để avoid rebuild
- **Embedding Cache**: Cache embeddings cho repeated queries
- **Model Selection**: Automatic fallback qua multiple Gemini models

### Optimization

- **Chunking**: Intelligent document splitting với overlap
- **Batch Processing**: Efficient embedding generation
- **Lazy Loading**: Initialize components on demand
- **Memory Management**: Optimized vector operations

## 🧪 Testing & Demo

### Run Demo

```bash
# Comprehensive demo với sample queries
python demo.py
```

### Example Queries

```python
# Technical questions
"Python có những đặc điểm gì nổi bật?"
"So sánh SQL và NoSQL databases"
"REST API best practices là gì?"

# Conversational follow-ups
"Có thể sử dụng Python để làm gì?"
"Ưu điểm của NoSQL là gì?"
"Có alternatives nào cho REST không?"
```

## 🔧 Development

### Adding New Documents

1. Update `data/mock_summaries.json`:

```json
{
  "id": "doc_new",
  "content": "Your document content...",
  "topic": "New Topic",
  "category": "New Category",
  "user_id": "user_id",
  "created_at": "2024-01-01T00:00:00Z",
  "tags": ["tag1", "tag2"]
}
```

2. Rebuild index:

```bash
python main.py --rebuild
```

### Custom Data Sources

```python
# Use custom JSON data
retriever = DocumentRetriever(data_path="/path/to/your/data.json")
chat_engine = RAGChatEngine(retriever=retriever)
```

### Extend LLM Integration

```python
# Custom LLM adapter
class CustomLLMAdapter:
    def generate_response(self, messages, config):
        # Your custom LLM logic
        pass

chat_engine = RAGChatEngine(llm_adapter=CustomLLMAdapter())
```

## 🚨 Troubleshooting

### Common Issues

**Index Not Found**

```bash
# Rebuild FAISS index
python main.py --rebuild
```

**API Key Issues**

```bash
# Check .env file
echo $GEMINI_API_KEY

# Test with canned responses
USE_CANNED_LLM=true python main.py
```

**Memory Issues**

```python
# Reduce chunk size và batch size
RetrievalConfig(chunk_size=100, top_k=3)
```

**Performance Issues**

```bash
# Clear cache và rebuild
curl -X POST http://localhost:8006/admin/clear-cache
curl -X POST http://localhost:8006/admin/rebuild-index
```

### Debug Mode

```bash
# Enable verbose logging
python main.py --verbose

# Check system stats
curl http://localhost:8006/stats
```

## 🔗 Integration

### Với Quiz Generator

```python
# Use RAG for generating quiz questions
retriever = get_document_retriever()
docs = retriever.search_by_filters(category="Programming")
# Pass docs to quiz generator
```

### Với Other Packages

```python
# Share retriever instance
from rag_chatbot import get_document_retriever
from other_package import SomeService

retriever = get_document_retriever()
service = SomeService(knowledge_base=retriever)
```

## 📈 Monitoring

### API Monitoring

- Health check: `GET /health`
- System stats: `GET /stats`
- Performance metrics trong response times

### Logging

- Structured logging với timestamps
- Request/response tracking
- Error monitoring và alerting

## 🛡️ Security

### API Security

- CORS configuration
- Input validation với Pydantic
- Rate limiting (có thể thêm middleware)
- Error handling không expose internals

### Data Privacy

- Local embedding models (no data sent to external services)
- Configurable data retention
- Conversation cleanup options

## 📚 Tài liệu bổ sung

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [Google Gemini API](https://ai.google.dev/)

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add tests cho new functionality
4. Update documentation
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.
