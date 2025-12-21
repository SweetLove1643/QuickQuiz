# RAG Chatbot Interface

## Overview

The Chatbot component provides an interactive interface for users to interact with the RAG (Retrieval-Augmented Generation) chatbot service. This allows users to ask questions about their documents and receive answers enhanced with relevant context from the document library.

## Features

- **Real-time Chat Interface**: Send messages and receive AI-powered responses
- **Document Context**: Chatbot retrieves relevant documents to answer questions
- **Conversation History**: Maintains conversation context across multiple messages
- **Source Attribution**: Shows retrieved documents that informed the response
- **Copy Functionality**: Users can easily copy assistant responses
- **Smart Suggestions**: Provides suggested questions when starting a new chat
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Usage

### Navigation

1. Click on "Chatbot" in the sidebar navigation menu
2. Optionally select a document from the library to provide context
3. Start asking questions in the input field

### Components

#### Chatbot Component (`Chatbot.tsx`)

Located at: `frontend/src/components/Chatbot.tsx`

**Props:**

- `documentId?: string` - ID of the document to provide context (optional)
- `documentName?: string` - Display name of the document (optional)

**Key Features:**

- Message management with user/assistant message types
- Real-time streaming of responses
- Source tracking and display
- Copy-to-clipboard functionality
- Suggested questions for new conversations

#### API Integration

The chatbot connects to the RAG Chatbot service at `http://localhost:8002/api`:

```typescript
POST /api/chat
{
  query: string,
  conversation_id?: string,
  document_id?: string,
  retrieval_config: {
    top_k: number,           // Number of documents to retrieve
    similarity_threshold: number  // Minimum similarity score
  },
  chat_config: {
    temperature: number,     // Response creativity (0-1)
    max_tokens: number       // Maximum response length
  }
}
```

**Response:**

```typescript
{
  answer: string,
  context: {
    retrieved_documents: string[]
  },
  processing_time: number
}
```

## Configuration

### Service Endpoints

- **RAG Chatbot Service**: `http://localhost:8002/api`
- **Default Retrieval Settings**:
  - `top_k: 5` - Returns top 5 relevant documents
  - `similarity_threshold: 0.3` - Filters results with 30%+ similarity
- **Default Chat Settings**:
  - `temperature: 0.7` - Balanced creativity/consistency
  - `max_tokens: 500` - Maximum response length

## User Experience

### Initial State

- Welcome message with instructions
- Suggested questions to get started
- Warning if no document is selected

### Chat Flow

1. User enters a question
2. System shows "Thinking..." indicator
3. Assistant provides answer with sources
4. User can copy response or ask follow-up questions

### Source Display

- Shows top 3 most relevant sources
- Displays similarity score for each source
- Allows users to verify answer accuracy

## Integration with Other Features

### Document Selection

Users can select any document from:

- Library page
- Popular Documents widget
- Recent documents in home

When a document is selected, it's automatically passed to the chatbot for context-enhanced responses.

### Quiz Integration

The chatbot can help:

- Clarify quiz questions
- Explain answer rationales
- Provide supplementary learning material

## Architecture

### Component Hierarchy

```
App (chatbot page)
├── Chatbot
│   ├── Message Display Area
│   ├── Suggested Questions (on first load)
│   └── Input Form
└── Document Context (optional)
```

### State Management

- `messages`: Array of chat messages
- `input`: Current input field value
- `isLoading`: Loading state for API calls
- `conversationId`: Unique identifier for conversation
- `copiedId`: Track which message's copy button was clicked

## Error Handling

- Network errors display user-friendly messages
- Failed requests show "Xin lỗi, tôi gặp lỗi..." message
- Input validation prevents empty messages
- Document requirement prevents chatbot use without context

## Accessibility

- Keyboard navigation supported
- Clear button labels and icons
- ARIA-friendly component structure
- High contrast text and backgrounds
- Mobile-responsive layout

## Performance Considerations

- Messages are virtualized in scroll area (prevents lag with long conversations)
- Auto-scroll to latest message on mobile
- Debounced input handling
- Efficient state updates using React hooks

## Future Enhancements

- [ ] Conversation saving and retrieval
- [ ] Multiple conversation sessions
- [ ] Advanced filtering options
- [ ] Document annotation during chat
- [ ] Export conversation as PDF
- [ ] Voice input/output
- [ ] Multi-language support
- [ ] Custom system prompts

## Troubleshooting

### Chatbot not responding

1. Check if RAG Chatbot service is running on port 8002
2. Verify document selection
3. Check browser console for error messages

### Sources not displaying

1. Ensure retrieval service is running
2. Check similarity threshold settings
3. Verify document indexing in database

### Service connection errors

1. Ensure all backend services are started with `./start_system.bat`
2. Check port availability (8002 for RAG Chatbot)
3. Verify CORS configuration in service

## API Service Details

**RAG Chatbot Service Location**: `services/rag_chatbot_service/`

Key files:

- `api.py` - FastAPI server and endpoints
- `chat_engine.py` - RAG chat processing logic
- `sqlite_retriever.py` - Document retrieval from database
- `schemas.py` - Request/response data models

For more details, see `services/rag_chatbot_service/README.md`
