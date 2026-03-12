#!/bin/bash

# Start background workers for email and campaign processing

echo "🚀 Starting Background Workers..."

# Start Redis if not running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "📦 Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Kill existing workers
echo "🔄 Stopping existing workers..."
pkill -f "run_email_worker.py" 2>/dev/null
pkill -f "run_campaign_worker.py" 2>/dev/null
sleep 2

# Start email worker in background
echo "📧 Starting Email Worker..."
cd /app/backend
nohup python -u run_email_worker.py > /var/log/email_worker.log 2>&1 &
EMAIL_WORKER_PID=$!
echo "   Email Worker PID: $EMAIL_WORKER_PID"

# Start campaign worker in background
echo "📢 Starting Campaign Worker..."
nohup python -u run_campaign_worker.py > /var/log/campaign_worker.log 2>&1 &
CAMPAIGN_WORKER_PID=$!
echo "   Campaign Worker PID: $CAMPAIGN_WORKER_PID"

sleep 3

# Check if workers are running
echo ""
echo "✅ Worker Status:"
if ps -p $EMAIL_WORKER_PID > /dev/null; then
    echo "   ✅ Email Worker: Running (PID: $EMAIL_WORKER_PID)"
else
    echo "   ❌ Email Worker: Failed to start"
fi

if ps -p $CAMPAIGN_WORKER_PID > /dev/null; then
    echo "   ✅ Campaign Worker: Running (PID: $CAMPAIGN_WORKER_PID)"
else
    echo "   ❌ Campaign Worker: Failed to start"
fi

echo ""
echo "📋 To monitor workers:"
echo "   tail -f /var/log/email_worker.log"
echo "   tail -f /var/log/campaign_worker.log"
echo ""
echo "🛑 To stop workers:"
echo "   pkill -f 'run_email_worker.py'"
echo "   pkill -f 'run_campaign_worker.py'"
