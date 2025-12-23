# QuickQuiz

Specialized Essay - AI-powered automated quiz creation and evaluation system.

## Features

- Extract text from documents (OCR)
- Automated document content summarization
- Create quizzes from documents
- Assignment assessment, grading, and detailed explanations
- RAG chatbot answers questions from documents
- User Management and Authentication (IAM)
- Interactive user interface

## Demo

[![Watch the video](https://img.youtube.com/vi/FouqV87yqoI/0.jpg)](https://www.youtube.com/watch?v=FouqV87yqoI)


## Architecture

The system is built according to the Microservices architecture:

![Project architecture](<images/Project architecture.png>)

- Frontend: ReactJS (Port 3000)
- API Gateway: Django (Port 8007) - Primary Communication Gateway
- IAM Service: Django (Port 8001) - Authentication Manager
- Quiz Generator: Python (Port 8002) - Question Generator
- Quiz Evaluator: Python (Port 8003) - Scoring
- OCR Service: FastAPI (Port 8004) - Image/PDF Processing
- Summary Service: FastAPI (Port 8005)
- RAG Chatbot: Python (Port 8006) - Virtual Assistant

## Tech Stack

- Client: React, TypeScript, TailwindCSS
- Server: Django, FastAPI, Python
- Database: SQLite (Each service has its own database)
- AI/LLM: Gemini, Qwen-VL, ViT5, RAG

## Installation

### Prerequisites

Hardware:

- Window 10 or later
- RTX 1650 graphics card or higher
  Software:
- Python 3.8+
- Node.js & npm
- Vs Code (recommended)

### Setup

1. Clone the project

```bash
git clone https://github.com/SweetLove1643/QuickQuiz.git
cd QuickQuiz
```

2. Create the environment and install the necessary libraries

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r ./requirements.txt
```

3. Create and configure the .env file

```bash
# Services
GEMINI_API_KEY =<your api key here>

GEMINI_MODEL=gemini-2.5-flash

# Django Gateway Configuration
DEBUG=True
DJANGO_SECRET_KEY=<your Django key here>
ALLOWED_HOSTS=localhost,127.0.0.1

# Logging
LOG_LEVEL=INFO
```

## Contributing

Contributions are always welcome!

See [Contributing.md](Contributing.md) for ways to get started.

## Support

For support, please email to [us](trinhuutho@gmail.com).

## License

This repo is under [MIT](LICENSE) license.

## Authors

- [@SweetLove1643](https://www.github.com/SweetLove1643)
- [@TrinhHuuTho](https://www.github.com/TrinhHuuTho)
