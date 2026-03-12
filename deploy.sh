#!/bin/bash

###############################################################################
# AI Email Assistant - Production Deployment Script
# 
# This script handles complete deployment from git pull to production ready
###############################################################################

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $1"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Parse command line arguments
GIT_BRANCH="main"
MONGODB_NAME="email_assistant_db"
SKIP_GIT=false
SKIP_DEPS=false
PRODUCTION_BUILD=true

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--branch)
            GIT_BRANCH="$2"
            shift 2
            ;;
        -d|--db-name)
            MONGODB_NAME="$2"
            shift 2
            ;;
        --skip-git)
            SKIP_GIT=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --dev)
            PRODUCTION_BUILD=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -b, --branch BRANCH     Git branch to deploy (default: main)"
            echo "  -d, --db-name NAME      MongoDB database name (default: email_assistant_db)"
            echo "  --skip-git              Skip git pull"
            echo "  --skip-deps             Skip dependency installation"
            echo "  --dev                   Run in development mode (no production build)"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --branch production --db-name my_email_db"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

###############################################################################
# START DEPLOYMENT
###############################################################################

print_header "AI Email Assistant - Production Deployment"

print_info "Configuration:"
print_info "  Git Branch: $GIT_BRANCH"
print_info "  MongoDB Database: $MONGODB_NAME"
print_info "  Production Build: $PRODUCTION_BUILD"
print_info "  Skip Git: $SKIP_GIT"
print_info "  Skip Dependencies: $SKIP_DEPS"
echo ""

###############################################################################
# 1. GIT OPERATIONS
###############################################################################

if [ "$SKIP_GIT" = false ]; then
    print_header "Step 1: Git Operations"
    
    if [ ! -d ".git" ]; then
        print_error "Not a git repository. Please run this script from the project root."
        exit 1
    fi
    
    print_info "Fetching latest changes..."
    git fetch origin
    
    print_info "Checking out branch: $GIT_BRANCH"
    git checkout "$GIT_BRANCH" || {
        print_error "Failed to checkout branch $GIT_BRANCH"
        exit 1
    }
    
    print_info "Pulling latest changes..."
    git pull origin "$GIT_BRANCH" || {
        print_error "Failed to pull from $GIT_BRANCH"
        exit 1
    }
    
    print_status "Git operations completed"
else
    print_warning "Skipping git operations"
fi

###############################################################################
# 2. SYSTEM DEPENDENCIES
###############################################################################

print_header "Step 2: System Dependencies"

# Check for required commands
REQUIRED_COMMANDS=("python3" "node" "npm" "mongod")
MISSING_COMMANDS=()

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command_exists "$cmd"; then
        MISSING_COMMANDS+=("$cmd")
    fi
done

if [ ${#MISSING_COMMANDS[@]} -gt 0 ]; then
    print_warning "Missing commands: ${MISSING_COMMANDS[*]}"
    print_info "Attempting to install missing dependencies..."
    
    # Update package lists
    sudo apt-get update -qq
    
    # Install missing packages
    for cmd in "${MISSING_COMMANDS[@]}"; do
        case $cmd in
            python3)
                sudo apt-get install -y python3 python3-pip python3-venv
                ;;
            node|npm)
                if ! command_exists node; then
                    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
                    sudo apt-get install -y nodejs
                fi
                ;;
            mongod)
                print_warning "MongoDB not found. Installing MongoDB..."
                wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
                echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
                sudo apt-get update -qq
                sudo apt-get install -y mongodb-org
                ;;
        esac
    done
fi

print_status "System dependencies verified"

###############################################################################
# 3. REDIS INSTALLATION & SETUP
###############################################################################

print_header "Step 3: Redis Setup"

if ! command_exists redis-server; then
    print_info "Installing Redis..."
    sudo apt-get install -y redis-server
    print_status "Redis installed"
else
    print_status "Redis already installed"
fi

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    print_info "Starting Redis server..."
    redis-server --daemonize yes --bind 127.0.0.1 --port 6379
    sleep 2
fi

# Verify Redis is running
if redis-cli ping > /dev/null 2>&1; then
    print_status "Redis is running"
else
    print_error "Redis failed to start"
    exit 1
fi

###############################################################################
# 4. MONGODB SETUP
###############################################################################

print_header "Step 4: MongoDB Setup"

# Check if MongoDB is running
if ! pgrep mongod > /dev/null; then
    print_info "Starting MongoDB..."
    
    # Create data directory if it doesn't exist
    sudo mkdir -p /data/db
    sudo chown -R mongodb:mongodb /data/db
    
    # Start MongoDB
    sudo systemctl start mongod || sudo mongod --fork --logpath /var/log/mongodb/mongod.log
    sleep 3
fi

# Verify MongoDB is running
if pgrep mongod > /dev/null; then
    print_status "MongoDB is running"
else
    print_error "MongoDB failed to start"
    exit 1
fi

print_info "Using database: $MONGODB_NAME"

###############################################################################
# 5. BACKEND SETUP
###############################################################################

print_header "Step 5: Backend Setup"

cd backend

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    print_warning ".env file not found, creating from template..."
    cat > .env << EOF
# MongoDB
MONGO_URL=mongodb://localhost:27017

# Database Name
DATABASE_NAME=$MONGODB_NAME

# JWT Secret (generate a secure random string)
JWT_SECRET=$(openssl rand -base64 32)

# Redis
REDIS_URL=redis://localhost:6379/0

# Google OAuth (Add your credentials)
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8001/api/oauth/google/callback

# Groq API (Optional - for AI features)
GROQ_API_KEY=your_groq_api_key_here

# Emergent LLM (Optional - for AI features)
EMERGENT_LLM_KEY=your_emergent_llm_key_here
EOF
    print_warning "Please update .env with your API keys and credentials"
fi

if [ "$SKIP_DEPS" = false ]; then
    print_info "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip -q
    
    # Install dependencies
    pip install -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ -q
    
    print_status "Backend dependencies installed"
else
    print_warning "Skipping backend dependency installation"
fi

cd ..

###############################################################################
# 6. FRONTEND SETUP
###############################################################################

print_header "Step 6: Frontend Setup"

cd frontend

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    print_warning "Frontend .env not found, creating..."
    cat > .env << EOF
REACT_APP_BACKEND_URL=http://localhost:8001/api
EOF
fi

if [ "$SKIP_DEPS" = false ]; then
    print_info "Installing Node dependencies..."
    
    # Check if yarn is installed
    if ! command_exists yarn; then
        print_info "Installing yarn..."
        npm install -g yarn
    fi
    
    # Install dependencies
    yarn install --silent
    
    print_status "Frontend dependencies installed"
else
    print_warning "Skipping frontend dependency installation"
fi

# Build production frontend
if [ "$PRODUCTION_BUILD" = true ]; then
    print_info "Creating optimized production build..."
    yarn build
    print_status "Production build created in frontend/build/"
else
    print_info "Skipping production build (development mode)"
fi

cd ..

###############################################################################
# 7. SUPERVISOR CONFIGURATION
###############################################################################

print_header "Step 7: Process Management Setup"

if command_exists supervisorctl; then
    print_info "Configuring supervisor..."
    
    # Create supervisor config if needed
    SUPERVISOR_CONF="/etc/supervisor/conf.d/email-assistant.conf"
    
    if [ ! -f "$SUPERVISOR_CONF" ]; then
        print_info "Creating supervisor configuration..."
        sudo tee $SUPERVISOR_CONF > /dev/null << EOF
[program:email-assistant-backend]
command=$(pwd)/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
directory=$(pwd)/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/email-assistant-backend.err.log
stdout_logfile=/var/log/email-assistant-backend.out.log
environment=PATH="$(pwd)/backend/venv/bin"

[program:email-assistant-frontend]
command=yarn start
directory=$(pwd)/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/email-assistant-frontend.err.log
stdout_logfile=/var/log/email-assistant-frontend.out.log
EOF
        
        sudo supervisorctl reread
        sudo supervisorctl update
        print_status "Supervisor configured"
    fi
    
    # Restart services
    print_info "Restarting services via supervisor..."
    sudo supervisorctl restart all
    sleep 3
    sudo supervisorctl status
else
    print_warning "Supervisor not found. You'll need to start services manually."
fi

###############################################################################
# 8. START WORKERS
###############################################################################

print_header "Step 8: Background Workers"

print_info "Background workers are integrated into the FastAPI backend"
print_info "Workers will start automatically when backend starts"
print_info "  • Email polling worker (every 60 seconds)"
print_info "  • Follow-up worker (every 5 minutes)"
print_info "  • Reminder worker (every 1 hour)"

###############################################################################
# 9. HEALTH CHECK
###############################################################################

print_header "Step 9: Health Check"

print_info "Waiting for services to start..."
sleep 5

# Check backend
if curl -s http://localhost:8001/api/health > /dev/null; then
    print_status "Backend API is responding"
else
    print_error "Backend API is not responding"
fi

# Check MongoDB
if mongosh --eval "db.adminCommand('ping')" --quiet $MONGODB_NAME > /dev/null 2>&1; then
    print_status "MongoDB is accessible"
else
    print_warning "MongoDB connection check failed (might be authentication)"
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    print_status "Redis is responding"
else
    print_error "Redis is not responding"
fi

###############################################################################
# DEPLOYMENT COMPLETE
###############################################################################

print_header "Deployment Complete!"

echo ""
print_status "Services Status:"
echo ""
print_info "  Backend API:     http://localhost:8001"
print_info "  Frontend:        http://localhost:3000"
print_info "  MongoDB:         mongodb://localhost:27017/$MONGODB_NAME"
print_info "  Redis:           redis://localhost:6379"
echo ""
print_info "  Backend Logs:    /var/log/email-assistant-backend.*.log"
print_info "  Frontend Logs:   /var/log/email-assistant-frontend.*.log"
echo ""

if [ "$PRODUCTION_BUILD" = true ]; then
    print_warning "Production build created. For production deployment:"
    print_info "  1. Serve frontend/build/ with nginx or similar"
    print_info "  2. Update REACT_APP_BACKEND_URL to production URL"
    print_info "  3. Configure SSL/TLS certificates"
    print_info "  4. Set up proper firewall rules"
    print_info "  5. Configure backup strategy for MongoDB"
fi

echo ""
print_status "Deployment completed successfully!"
echo ""

# Show next steps
print_header "Next Steps"
echo ""
print_info "1. Verify all services are running:"
echo "   sudo supervisorctl status"
echo ""
print_info "2. Check backend logs:"
echo "   tail -f /var/log/email-assistant-backend.err.log"
echo ""
print_info "3. Check frontend in browser:"
echo "   http://localhost:3000"
echo ""
print_info "4. Update environment variables in:"
echo "   - backend/.env (API keys, OAuth credentials)"
echo "   - frontend/.env (Backend URL for production)"
echo ""
print_info "5. Create initial user and seed data:"
echo "   cd backend && python create_seed_for_amit.py"
echo ""

exit 0
