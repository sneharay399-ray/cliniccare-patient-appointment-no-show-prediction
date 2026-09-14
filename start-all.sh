#!/bin/bash
# start-all.sh — convenience script to start all three services

echo "Starting ClinicCare services..."

# Start ML service in background
cd ml-service && python app.py &
ML_PID=$!
echo "ML Service started (PID $ML_PID) on :5001"

# Start backend in background
cd ../backend && npm start &
BACKEND_PID=$!
echo "Backend started (PID $BACKEND_PID) on :4000"

# Start frontend dev server
cd ../frontend && npm run dev &
FRONTEND_PID=$!
echo "Frontend started (PID $FRONTEND_PID) on :5173"

echo ""
echo "All services running:"
echo "  Frontend:   http://localhost:5173"
echo "  Backend:    http://localhost:4000"
echo "  ML Service: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop all services"

wait
