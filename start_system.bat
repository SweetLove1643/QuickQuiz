@echo off
REM QuickQuiz System Startup Script for Windows
REM Starts all services in the correct order

echo Starting QuickQuiz System...

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo Installing/updating dependencies...
pip install -q -r requirements.txt >nul 2>&1 || echo No requirements.txt found

echo.
echo Starting microservices...

REM Start IAM Service (Authentication & User Management) - FIRST
echo Starting IAM Service (port 8005)...
start "IAM Service" /min cmd /c "cd services\iam_service && python manage.py runserver 0.0.0.0:8005"

REM Wait for IAM service to start (it's needed by gateway)
echo Waiting for IAM Service to initialize...
timeout /t 5 /nobreak >nul

REM Start Quiz Generator Service
echo Starting Quiz Generator (port 8003)...
start "Quiz Generator" /min cmd /c "cd services\quiz_generator_service && python -m uvicorn api:app --host 127.0.0.1 --port 8003 --reload"

REM Start Quiz Evaluator Service
echo Starting Quiz Evaluator (port 8004)...
start "Quiz Evaluator" /min cmd /c "cd services\quiz_evaluator_service && python -m uvicorn api:app --host 127.0.0.1 --port 8004 --reload"

REM Start OCR Service
echo Starting OCR Service (port 8007)...
start "OCR Service" /min cmd /c "cd services\ocr_service && python -m uvicorn api:app --host 127.0.0.1 --port 8007 --reload"

REM Start Summary Service
echo Starting Summary Service (port 8008)...
start "Summary Service" /min cmd /c "cd services\summary_service && python -m uvicorn api:app --host 127.0.0.1 --port 8008 --reload"

REM Start RAG Chatbot Service
echo Starting RAG Chatbot (port 8002)...
start "RAG Chatbot" /min cmd /c "cd services\rag_chatbot_service && python -m uvicorn api:app --host 127.0.0.1 --port 8002 --reload"

REM Wait a moment for services to start
echo Waiting for services to initialize...
timeout /t 8 /nobreak >nul

REM Start Django API Gateway
echo Starting API Gateway (port 8001)...
start "API Gateway" /min cmd /c "cd services\gateway_service && python manage.py runserver 0.0.0.0:8001"

REM Wait for gateway to start
echo Waiting for gateway to initialize...
timeout /t 3 /nobreak >nul

REM Start Frontend React App
echo Starting Frontend (port 3000)...
start "Frontend React" /min cmd /c "cd frontend && npm run dev"

REM Wait for gateway to start
echo Waiting for gateway to initialize...
timeout /t 3 /nobreak >nul

echo.
echo QuickQuiz System is now running!
echo.
echo Service URLs:
echo    - Frontend:         http://localhost:3000
echo    - API Gateway:      http://localhost:8001
echo    - IAM Service:      http://localhost:8005
echo    - RAG Chatbot:      http://localhost:8002
echo    - Quiz Generator:   http://localhost:8003
echo    - Quiz Evaluator:   http://localhost:8004
echo    - OCR Service:      http://localhost:8007
echo    - Summary Service:  http://localhost:8008
echo.
echo Important Endpoints:
echo    - Web Interface:       http://localhost:3000
echo    - Health Check:        http://localhost:8001/api/health/
echo    - API Docs:           http://localhost:8001/api/
echo    - IAM Admin:          http://localhost:8005/admin/
echo    - Login:              POST http://localhost:8005/api/users/login/
echo    - User Profile:       GET http://localhost:8005/api/users/me/
echo    - Generate Quiz:      POST http://localhost:8001/api/quiz/generate/
echo    - Evaluate Quiz:      POST http://localhost:8001/api/quiz/evaluate/
echo    - Chat (RAG):         POST http://localhost:8001/api/chat/
echo    - Extract Text:       POST http://localhost:8001/api/ocr/extract_text_multi/
echo    - Summarize Text:     POST http://localhost:8001/api/summary/summarize_text/
echo.
echo Admin Credentials:
echo    - Username: admin
echo    - Password: Admin123
echo.
echo To stop services, close the individual terminal windows
echo    or use Task Manager to end Python processes

pause