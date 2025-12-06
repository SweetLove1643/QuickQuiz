# QuickQuiz - Complete Learning Platform

🎯 **Intelligent quiz generation and learning platform with AI-powered features**

## 🌟 Features

- 📝 **Smart Quiz Generation** - Create quizzes from any content
- 🔍 **OCR Document Processing** - Extract text from images/PDFs
- 📋 **AI Summarization** - Automatically summarize long content
- 🧠 **RAG Chatbot** - Interactive Q&A with your documents
- ✅ **Auto Evaluation** - Intelligent quiz grading and feedback
- 🎨 **Modern UI** - Clean, responsive interface with dark/light themes

## 🏗️ Architecture

**Microservices Backend:**

- 🌐 **API Gateway** (Port 8001) - Unified entry point
- 🧩 **Quiz Generator** (Port 8003) - Quiz creation service
- ✅ **Quiz Evaluator** (Port 8005) - Answer evaluation service
- 👁️ **OCR Service** (Port 8007) - Document text extraction
- 📄 **Summary Service** (Port 8009) - Content summarization
- 💬 **RAG Chatbot** (Port 8011) - Conversational AI

**Frontend:**

- ⚡ **React + TypeScript** (Port 3000) - Modern web interface
- 🎨 **Radix UI + Tailwind** - Beautiful, accessible components

## 🚀 Quick Start

### 1. Start Backend Services

```bash
# Clone and setup
git clone https://github.com/SweetLove1643/QuickQuiz.git
cd QuickQuiz

# Start all microservices
./start_system.bat  # Windows
# or
./start_system.sh   # Linux/Mac
```

### 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Access Application

- 🌐 **Frontend**: http://localhost:3000
- 📡 **API Gateway**: http://localhost:8001
- 📊 **Health Check**: http://localhost:8001/api/health/

## 📖 Usage Guide

### Creating Quizzes

1. Upload document or paste text
2. Configure quiz settings (question count, types)
3. Generate quiz with AI
4. Take quiz and get instant feedback

### Document Processing

1. Upload images/PDFs via OCR service
2. Get extracted text automatically
3. Summarize long content
4. Ask questions via RAG chatbot

## 🛠️ Development

### Backend Requirements

- Python 3.8+
- FastAPI
- SQLite
- Gemini AI API

### Frontend Requirements

- Node.js 18+
- React 18
- TypeScript
- Vite

### Project Structure

```
QuickQuiz/
├── services/           # Backend microservices
│   ├── gateway_service/    # API Gateway (Django)
│   ├── quiz_generator_service/     # Quiz creation
│   ├── quiz_evaluator_service/     # Quiz grading
│   ├── ocr_service/               # OCR processing
│   ├── summary_service/           # Text summarization
│   └── rag_chatbot_service/       # Conversational AI
├── frontend/          # React frontend
├── start_system.bat   # Windows startup
└── start_system.sh    # Linux startup
```

## 🎯 System Status

All services healthy and fully integrated! ✅

---

**Built with ❤️ using modern microservices architecture**
