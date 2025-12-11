@echo off
REM ====================================================================
REM QuickQuiz System Startup Script for Windows
REM ====================================================================
REM Starts all services in priority order:
REM 1. IAM Service (Authentication - required first)
REM 2. Microservices (can start in parallel)
REM 3. API Gateway (needs microservices ready)
REM 4. Frontend (needs gateway ready)
REM ====================================================================

REM ====================================================================
REM CONFIGURATION SECTION - Customize here
REM ====================================================================

REM Port Configuration (sorted by startup order)
set IAM_PORT=8001
set QUIZ_GENERATOR_PORT=8002
set QUIZ_EVALUATOR_PORT=8003
set OCR_PORT=8004
set SUMMARY_PORT=8005
set RAG_CHATBOT_PORT=8006
set GATEWAY_PORT=8007
set FRONTEND_PORT=3000

REM Service Host Configuration
set SERVICE_HOST=127.0.0.1
set GATEWAY_HOST=0.0.0.0
set IAM_HOST=0.0.0.0

REM Startup Delays (in seconds)
set IAM_INIT_DELAY=5
set SERVICES_INIT_DELAY=8
set GATEWAY_INIT_DELAY=3
set FRONTEND_INIT_DELAY=2

REM Window Style (min = minimized, normal = normal window)
set WINDOW_STYLE=min

REM Development Mode (reload = auto-reload on code changes)
set DEV_MODE=reload

REM ====================================================================
REM END OF CONFIGURATION SECTION
REM ====================================================================

echo.
echo ====================================================================
echo           QuickQuiz System Startup
echo ====================================================================
echo Configuration:
echo   - IAM Port:           %IAM_PORT%
echo   - Gateway Port:       %GATEWAY_PORT%
echo   - Frontend Port:      %FRONTEND_PORT%
echo   - Window Style:       %WINDOW_STYLE%
echo   - Dev Mode:           %DEV_MODE%
echo ====================================================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo Installing/updating dependencies...
pip install -q -r requirements.txt >nul 2>&1 || echo No requirements.txt found

REM ====================================================================
REM STEP 1: Start IAM Service (Authentication - Required First)
REM ====================================================================
echo [1/4] Starting IAM Service (Port %IAM_PORT%)...
start "IAM Service - Port %IAM_PORT%" /%WINDOW_STYLE% cmd /c "cd services\iam_service && python manage.py runserver %IAM_HOST%:%IAM_PORT%"

echo       Waiting %IAM_INIT_DELAY% seconds for IAM to initialize...
timeout /t %IAM_INIT_DELAY% /nobreak >nul
echo       [OK] IAM Service ready
echo.

REM ====================================================================
REM STEP 2: Start Microservices (Can run in parallel)
REM ====================================================================
echo [2/4] Starting Microservices...
echo       - Quiz Generator (Port %QUIZ_GENERATOR_PORT%)
start "Quiz Generator - Port %QUIZ_GENERATOR_PORT%" /%WINDOW_STYLE% cmd /c "cd services\quiz_generator_service && python api.py"

echo       - Quiz Evaluator (Port %QUIZ_EVALUATOR_PORT%)
start "Quiz Evaluator - Port %QUIZ_EVALUATOR_PORT%" /%WINDOW_STYLE% cmd /c "cd services\quiz_evaluator_service && python api.py"

echo       - OCR Service (Port %OCR_PORT%)
start "OCR Service - Port %OCR_PORT%" /%WINDOW_STYLE% cmd /c "cd services\ocr_service && python api.py"

echo       - Summary Service (Port %SUMMARY_PORT%)
start "Summary Service - Port %SUMMARY_PORT%" /%WINDOW_STYLE% cmd /c "cd services\summary_service && python api.py"

echo       - RAG Chatbot (Port %RAG_CHATBOT_PORT%)
start "RAG Chatbot - Port %RAG_CHATBOT_PORT%" /%WINDOW_STYLE% cmd /c "cd services\rag_chatbot_service && python api.py"

echo       Waiting %SERVICES_INIT_DELAY% seconds for microservices to initialize...
timeout /t %SERVICES_INIT_DELAY% /nobreak >nul
echo       [OK] All microservices ready
echo.

REM ====================================================================
REM STEP 3: Start API Gateway (Needs microservices ready)
REM ====================================================================
echo [3/4] Starting API Gateway (Port %GATEWAY_PORT%)...
start "API Gateway - Port %GATEWAY_PORT%" /%WINDOW_STYLE% cmd /c "cd services\gateway_service && python manage.py runserver %GATEWAY_HOST%:%GATEWAY_PORT%"

echo       Waiting %GATEWAY_INIT_DELAY% seconds for gateway to initialize...
timeout /t %GATEWAY_INIT_DELAY% /nobreak >nul
echo       [OK] Gateway ready
echo.

REM ====================================================================
REM STEP 4: Start Frontend (Needs gateway ready)
REM ====================================================================
echo [4/4] Starting Frontend (Port %FRONTEND_PORT%)...
start "Frontend - Port %FRONTEND_PORT%" /%WINDOW_STYLE% cmd /c "cd frontend && npm run dev"
 ====================================================================
echo                QuickQuiz System is Running!
echo ====================================================================
echo.
echo Main URLs:
echo    Frontend:         http://localhost:%FRONTEND_PORT%
echo    API Gateway:      http://localhost:%GATEWAY_PORT%
echo    API Health:       http://localhost:%GATEWAY_PORT%/api/health/
echo.
echo Backend Services (in startup order):
echo    1. IAM Service:      http://localhost:%IAM_PORT% (Admin: /admin/)
echo    2. Quiz Generator:   http://localhost:%QUIZ_GENERATOR_PORT%
echo    3. Quiz Evaluator:   http://localhost:%QUIZ_EVALUATOR_PORT%
echo    4. OCR Service:      http://localhost:%OCR_PORT%
echo    5. Summary Service:  http://localhost:%SUMMARY_PORT%
echo    6. RAG Chatbot:      http://localhost:%RAG_CHATBOT_PORT%
echo    - IAM Service:      http://localhost:8005 (Admin: http://localhost:8005/admin/)
echo    - RAG Chatbot:      http://localhost:8002
echo    - Quiz Generator:   http://localhost:8003
echo    - Quiz Evaluator:   http://localhost:8004
echo    - OCR Service:      http://localhost:8007
echo    - Summary Service:  http://localhost:8008
echo.
echo Database Files:
echo    - IAM:              services\iam_service\data\iam.db
echo    - Quiz Generator:   services\quiz_generator_service\quiz_generator_service.db
echo    - Quiz Evaluator:   services\quiz_evaluator_service\quiz_evaluator_service.db
echo    - RAG Chatbot:      services\rag_chatbot_service\rag_chatbot.db
echo    - OCR Service:      services\ocr_service\ocr_service.db
echo    - Summary Service:  services\summary_service\summary_service.db
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
echo ====================================================================
echo Configuration Tips:
echo ====================================================================
echo To customize ports, delays, or window style:
echo    1. Edit the CONFIGURATION SECTION at the top of this file
echo    2. Change variables like:
echo       - set GATEWAY_PORT=8001
echo       - set WINDOW_STYLE=normal    (or 'min' for minimized)
echo       - set IAM_INIT_DELAY=5       (seconds)
echo.
echo To stop services:
echo    - Close individual terminal windows, or
echo    - Use Task Manager to end Python/Node processes
echo ====================================================================
echo.echo    - Password: Admin123
echo.
echo To stop services, close the individual terminal windows
echo    or use Task Manager to end Python processes

pause