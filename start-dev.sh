#!/bin/bash

echo "🚀 Starting SIHP-IntelRisk Development Environment"
echo "=================================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
if ! command_exists node; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."

if [ ! -d "Back-End/node_modules" ]; then
    echo "Installing backend dependencies..."
    cd Back-End && npm install && cd ..
fi

if [ ! -d "Front-End/node_modules" ]; then
    echo "Installing frontend dependencies..."
    cd Front-End && npm install && cd ..
fi

# Create .env files if they don't exist
if [ ! -f "Back-End/.env" ]; then
    echo "📝 Creating backend .env file..."
    cp Back-End/.env.example Back-End/.env
fi

if [ ! -f "Front-End/.env" ]; then
    echo "📝 Creating frontend .env file..."
    echo "VITE_API_BASE_URL=http://localhost:3001/api/v1" > Front-End/.env
fi

echo ""
echo "🎯 Starting services..."
echo "Backend will run on: http://localhost:3001"
echo "Frontend will run on: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start both services
trap 'kill $(jobs -p)' EXIT

# Start backend
cd Back-End && npm run dev &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend
cd Front-End && npm run dev &
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID