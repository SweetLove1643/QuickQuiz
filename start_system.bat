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

REM Start Quiz Generator Service
echo Starting Quiz Generator (port 8003)...
start "Quiz Generator" /min cmd /c "cd services\quiz_generator && python -m uvicorn api:app --host 127.0.0.1 --port 8003 --reload"

REM Start Quiz Evaluator Service
echo Starting Quiz Evaluator (port 8005)...
start "Quiz Evaluator" /min cmd /c "cd services\quiz_evaluator && python -m uvicorn api:app --host 127.0.0.1 --port 8005 --reload"

REM Wait a moment for services to start
echo Waiting for services to initialize...
timeout /t 5 /nobreak >nul

REM Start Django API Gateway
echo Starting API Gateway (port 8001)...
start "API Gateway" /min cmd /c "cd services\gateway_service && python manage.py runserver 127.0.0.1:8001"

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
echo    - Quiz Generator:   http://localhost:8003
echo    - Quiz Evaluator:   http://localhost:8005
echo.
echo Important Endpoints:
echo    - Web Interface:    http://localhost:3000
echo    - Health Check:     http://localhost:8001/api/health/
echo    - API Docs:        http://localhost:8001/api/
echo    - Generate Quiz:    POST http://localhost:8001/api/quiz/generate/
echo    - Evaluate Quiz:    POST http://localhost:8001/api/quiz/evaluate/
echo.
echo To stop services, close the individual terminal windows
echo    or use Task Manager to end Python processes

pause