#!/bin/bash

# QuickQuiz System Startup Script
# Starts all services in the correct order
# Operating System: Cross-platform (Linux, Mac, Windows with Git Bash)

echo "Starting QuickQuiz System..."

# Function to check if port is in use
check_port() {
    local port=$1
    if netstat -an | grep ":$port " > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "$service_name is ready!"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - waiting 2 seconds..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "$service_name failed to start within timeout"
    return 1
}

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtual environment..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate      # Linux/Mac
    elif [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate  # Windows Git Bash
    else
        echo "⚠️ Virtual environment not found. Please create one first:"
        echo "   python -m venv .venv"
        exit 1
    fi
fi

echo "Installing/updating dependencies..."
pip install -q -r requirements.txt 2>/dev/null || echo "No requirements.txt found"

# Start services in order
echo ""
echo "Starting microservices..."

# 1. Quiz Generator Service
echo "Starting Quiz Generator (port 8003)..."
cd services/quiz_generator
python -m uvicorn api:app --host 127.0.0.1 --port 8003 --reload &
QUIZ_GEN_PID=$!
cd ../..

# 2. Quiz Evaluator Service  
echo "Starting Quiz Evaluator (port 8005)..."
cd services/quiz_evaluator
python -m uvicorn api:app --host 127.0.0.1 --port 8005 --reload &
QUIZ_EVAL_PID=$!
cd ../..

# 3. Wait for microservices to be ready
wait_for_service "http://localhost:8003/health" "Quiz Generator"
wait_for_service "http://localhost:8005/health" "Quiz Evaluator"

# 4. Django API Gateway
echo "Starting API Gateway (port 8001)..."
cd services/gateway_service
python manage.py runserver 127.0.0.1:8001 &
GATEWAY_PID=$!
cd ../..

# Wait for gateway to be ready
wait_for_service "http://localhost:8001/api/health/" "API Gateway"

echo ""
echo "QuickQuiz System is now running!"
echo ""
echo "Service URLs:"
echo "   API Gateway:      http://localhost:8001"
echo "   Quiz Generator:   http://localhost:8003"
echo "   Quiz Evaluator:   http://localhost:8005"
echo ""
echo "Important Endpoints:"
echo "   Health Check:     http://localhost:8001/api/health/"
echo "   API Docs:        http://localhost:8001/api/"
echo "   Generate Quiz:    POST http://localhost:8001/api/quiz/generate/"
echo "   Evaluate Quiz:    POST http://localhost:8001/api/quiz/evaluate/"
echo ""
echo "Press Ctrl+C to stop all services"

# Store PIDs for cleanup
echo "$QUIZ_GEN_PID $QUIZ_EVAL_PID $GATEWAY_PID" > .service_pids

# Wait for user interrupt
trap 'kill $(cat .service_pids 2>/dev/null) 2>/dev/null; rm -f .service_pids; echo ""; echo "🛑 All services stopped"; exit 0' INT

# Keep script running
wait