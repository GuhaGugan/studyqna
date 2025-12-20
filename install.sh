#!/bin/bash

################################################################################
# StudyQnA Assistant - Complete Automated Installation Script
# This script automates the entire installation process on Ubuntu 22.04
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
APP_USER="studyqna"
APP_DIR="/home/${APP_USER}/studyqna"
DB_NAME="studyqna"
DB_USER="studyqna_user"
STATIC_IP=""  # Will be prompted
DOMAIN=""     # Will be prompted (optional)

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then 
        print_error "Please do not run this script as root. It will use sudo when needed."
        exit 1
    fi
}

# Function to check Ubuntu version
check_ubuntu() {
    if [ ! -f /etc/os-release ]; then
        print_error "Cannot detect OS version. This script is for Ubuntu 22.04."
        exit 1
    fi
    
    . /etc/os-release
    if [ "$ID" != "ubuntu" ] || [ "$VERSION_ID" != "22.04" ]; then
        print_warning "This script is designed for Ubuntu 22.04. Current OS: $ID $VERSION_ID"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Function to get user input
get_user_input() {
    echo
    print_info "=== Configuration Setup ==="
    echo
    print_info "Domain/IP Configuration:"
    echo "  - If you have a domain name (e.g., studyqna.com), enter it below"
    echo "  - If you don't have a domain, enter your server's static IP address"
    echo "  - You can skip both and configure later, but you'll need at least one"
    echo
    
    read -p "Enter your domain name (e.g., studyqna.com) or press Enter to skip: " DOMAIN
    
    if [ -z "$DOMAIN" ]; then
        read -p "Enter your static IP address (e.g., 54.123.45.67) or press Enter to skip: " STATIC_IP
        if [ -z "$STATIC_IP" ]; then
            print_warning "No domain or IP provided. The script will use server's default IP."
            STATIC_IP=$(hostname -I | awk '{print $1}')
            print_info "Using detected IP: $STATIC_IP"
        fi
    else
        print_info "Domain provided: $DOMAIN"
        print_info "You can get SSL certificate after installation with: sudo certbot --nginx -d $DOMAIN"
    fi
    
    echo
    print_info "Database Configuration:"
    read -sp "Enter database password for ${DB_USER}: " DB_PASSWORD
    echo
    read -sp "Confirm database password: " DB_PASSWORD_CONFIRM
    echo
    
    if [ "$DB_PASSWORD" != "$DB_PASSWORD_CONFIRM" ]; then
        print_error "Passwords do not match!"
        exit 1
    fi
    
    if [ -z "$DB_PASSWORD" ]; then
        print_error "Database password cannot be empty!"
        exit 1
    fi
}

# Step 1: Update system
update_system() {
    print_info "Step 1/12: Updating system packages..."
    sudo apt update
    sudo apt upgrade -y
    print_success "System updated"
}

# Step 2: Install essential tools
install_essentials() {
    print_info "Step 2/12: Installing essential tools..."
    sudo apt install -y curl wget git build-essential software-properties-common
    print_success "Essential tools installed"
}

# Step 3: Create application user
create_app_user() {
    print_info "Step 3/12: Creating application user..."
    
    if id "$APP_USER" &>/dev/null; then
        print_warning "User $APP_USER already exists. Skipping user creation."
    else
        sudo adduser --disabled-password --gecos "" "$APP_USER"
        sudo usermod -aG sudo "$APP_USER"
        print_success "User $APP_USER created"
    fi
}

# Step 4: Setup firewall
setup_firewall() {
    print_info "Step 4/12: Setting up firewall..."
    sudo apt install -y ufw
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo "y" | sudo ufw enable
    print_success "Firewall configured"
}

# Step 5: Setup swap
setup_swap() {
    print_info "Step 5/12: Setting up swap memory..."
    
    if [ -f /swapfile ]; then
        print_warning "Swap file already exists. Skipping swap setup."
    else
        sudo fallocate -l 2G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        print_success "Swap memory configured (2GB)"
    fi
}

# Step 6: Install PostgreSQL
install_postgresql() {
    print_info "Step 6/12: Installing PostgreSQL..."
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Create database and user
    sudo -u postgres psql <<EOF
CREATE DATABASE ${DB_NAME};
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
ALTER ROLE ${DB_USER} SET client_encoding TO 'utf8';
ALTER ROLE ${DB_USER} SET default_transaction_isolation TO 'read committed';
ALTER ROLE ${DB_USER} SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
\q
EOF
    
    print_success "PostgreSQL installed and configured"
}

# Step 7: Install Python and dependencies
install_python() {
    print_info "Step 7/12: Installing Python 3.11 and dependencies..."
    sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
    sudo apt install -y libpq-dev pkg-config
    sudo apt install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev
    sudo apt install -y libopencv-dev python3-opencv
    sudo apt install -y poppler-utils
    sudo apt install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
        libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
        libxfixes3 libxrandr2 libgbm1 libasound2
    print_success "Python and system dependencies installed"
}

# Step 8: Install Node.js
install_nodejs() {
    print_info "Step 8/12: Installing Node.js 18..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    print_success "Node.js installed"
}

# Step 9: Setup backend
setup_backend() {
    print_info "Step 9/12: Setting up backend..."
    
    # Create directories
    sudo mkdir -p "$APP_DIR/backend"
    sudo mkdir -p "$APP_DIR/backend/storage"
    sudo mkdir -p "$APP_DIR/backend/app/fonts"
    sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    
    # Note: Code should already be in place, but we'll setup the environment
    if [ ! -d "$APP_DIR/backend/venv" ]; then
        sudo -u "$APP_USER" bash <<EOF
cd "$APP_DIR/backend"
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
EOF
        print_success "Python virtual environment created"
    else
        print_warning "Virtual environment already exists. Skipping creation."
    fi
    
    # Download fonts
    print_info "Downloading multilingual fonts..."
    sudo -u "$APP_USER" bash <<EOF
cd "$APP_DIR/backend/app/fonts"
wget -q https://github.com/google/fonts/raw/main/ofl/notosans/NotoSans-Regular.ttf || true
wget -q https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf || true
wget -q https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf || true
wget -q https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansTelugu/NotoSansTelugu-Regular.ttf || true
wget -q https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansKannada/NotoSansKannada-Regular.ttf || true
wget -q https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansMalayalam/NotoSansMalayalam-Regular.ttf || true
wget -q https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansArabic/NotoSansArabic-Regular.ttf || true
EOF
    
    print_success "Backend setup completed"
    print_warning "NOTE: You need to install Python dependencies manually:"
    print_warning "  cd $APP_DIR/backend && source venv/bin/activate && pip install -r requirements.txt"
    print_warning "  playwright install chromium"
}

# Step 10: Setup frontend
setup_frontend() {
    print_info "Step 10/12: Setting up frontend..."
    
    if [ -d "$APP_DIR/frontend" ]; then
        print_info "Installing frontend dependencies..."
        sudo -u "$APP_USER" bash <<EOF
cd "$APP_DIR/frontend"
npm install
EOF
        print_success "Frontend dependencies installed"
        print_warning "NOTE: You need to build frontend manually:"
        print_warning "  cd $APP_DIR/frontend && npm run build"
    else
        print_warning "Frontend directory not found. Skipping frontend setup."
    fi
}

# Step 11: Install and configure Nginx
setup_nginx() {
    print_info "Step 11/12: Installing and configuring Nginx..."
    sudo apt install -y nginx
    
    # Determine server name
    if [ -n "$DOMAIN" ]; then
        SERVER_NAME="$DOMAIN www.$DOMAIN"
        print_info "Nginx configured for domain: $SERVER_NAME"
    elif [ -n "$STATIC_IP" ]; then
        SERVER_NAME="$STATIC_IP"
        print_info "Nginx configured for IP: $STATIC_IP"
    else
        SERVER_NAME="_"
        print_warning "No domain or IP configured. Using default server."
    fi
    
    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/studyqna > /dev/null <<EOF
server {
    listen 80;
    server_name ${SERVER_NAME};

    # Frontend
    location / {
        root ${APP_DIR}/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    # Static files caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)\$ {
        root ${APP_DIR}/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File upload size limit (100MB for large PDFs and mobile photos)
    client_max_body_size 100M;
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/studyqna /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test and reload
    sudo nginx -t
    sudo systemctl reload nginx
    sudo systemctl enable nginx
    
    print_success "Nginx configured"
}

# Step 12: Create systemd service
create_systemd_service() {
    print_info "Step 12/12: Creating systemd service..."
    
    sudo tee /etc/systemd/system/studyqna-backend.service > /dev/null <<EOF
[Unit]
Description=StudyQnA Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}/backend
Environment="PATH=${APP_DIR}/backend/venv/bin"
ExecStart=${APP_DIR}/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    sudo systemctl enable studyqna-backend
    
    print_success "Systemd service created"
    print_warning "NOTE: Service will be started after .env file is configured"
}

# Step 13: Setup SSL (optional)
setup_ssl() {
    if [ -n "$DOMAIN" ]; then
        print_info "Setting up SSL certificate..."
        sudo apt install -y certbot python3-certbot-nginx
        
        print_info "To get SSL certificate, run:"
        print_info "  sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
        print_warning "Make sure your domain DNS points to this server's IP first!"
    else
        print_info "Skipping SSL setup (no domain provided)"
    fi
}

# Create .env template
create_env_template() {
    print_info "Creating .env file template..."
    
    # Generate a random secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || echo "CHANGE_THIS_SECRET_KEY")
    
    sudo -u "$APP_USER" tee "$APP_DIR/backend/.env" > /dev/null <<EOF
# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}

# ============================================
# JWT SECURITY
# ============================================
SECRET_KEY=${SECRET_KEY}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ============================================
# ADMIN CONFIGURATION
# ============================================
ADMIN_EMAIL=admin@example.com

# ============================================
# STORAGE CONFIGURATION
# ============================================
STORAGE_PATH=${APP_DIR}/backend/storage
ENCRYPT_STORAGE=true

# ============================================
# EMAIL CONFIGURATION
# ============================================
EMAIL_PROVIDER=brevo
BREVO_API_KEY=your-brevo-api-key-here
BREVO_FROM_EMAIL=noreply@yourdomain.com
BREVO_FROM_NAME=StudyQnA

# ============================================
# OPENAI CONFIGURATION
# ============================================
OPENAI_API_KEY=sk-your-openai-api-key-here

# ============================================
# APPLICATION CONFIGURATION
# ============================================
APP_NAME=StudyQnA Generator
APP_URL=${DOMAIN:+https://${DOMAIN}}${DOMAIN:-http://${STATIC_IP}}

# ============================================
# CORS CONFIGURATION
# ============================================
CORS_ORIGINS_LIST=${DOMAIN:+https://${DOMAIN},https://www.${DOMAIN}}${DOMAIN:-http://${STATIC_IP}}

# ============================================
# AI USAGE TRACKING
# ============================================
AI_USAGE_THRESHOLD_TOKENS=1000000
AI_USAGE_ALERT_EMAIL=admin@yourdomain.com
EOF
    
    sudo chmod 600 "$APP_DIR/backend/.env"
    print_success ".env file template created at $APP_DIR/backend/.env"
    print_warning "IMPORTANT: Edit .env file and add your actual API keys!"
}

# Print summary
print_summary() {
    echo
    print_success "=========================================="
    print_success "Installation Complete!"
    print_success "=========================================="
    echo
    print_info "Next steps:"
    echo "1. Edit .env file: nano $APP_DIR/backend/.env"
    echo "   - Add your OpenAI API key"
    echo "   - Add your Brevo API key (or SMTP credentials)"
    echo "   - Update ADMIN_EMAIL"
    echo "   - Update APP_URL and CORS_ORIGINS_LIST"
    echo
    echo "2. Install Python dependencies:"
    echo "   cd $APP_DIR/backend"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo "   playwright install chromium"
    echo
    echo "3. Initialize database:"
    echo "   cd $APP_DIR/backend"
    echo "   source venv/bin/activate"
    echo "   python init_db.py"
    echo
    echo "4. Build frontend:"
    echo "   cd $APP_DIR/frontend"
    echo "   npm run build"
    echo
    echo "5. Start backend service:"
    echo "   sudo systemctl start studyqna-backend"
    echo "   sudo systemctl status studyqna-backend"
    echo
    if [ -n "$DOMAIN" ]; then
        echo "6. Setup SSL certificate:"
        echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
        echo
    fi
    echo "7. Access your application:"
    if [ -n "$DOMAIN" ]; then
        echo "   http://$DOMAIN (or https://$DOMAIN after SSL setup)"
        echo "   After SSL: https://$DOMAIN"
    elif [ -n "$STATIC_IP" ]; then
        echo "   http://$STATIC_IP"
    else
        DETECTED_IP=$(hostname -I | awk '{print $1}')
        echo "   http://$DETECTED_IP"
    fi
    echo
    print_info "Where Domain/IP are used:"
    echo "  - Nginx server_name: ${SERVER_NAME:-_}"
    echo "  - .env APP_URL: $(grep '^APP_URL=' "$APP_DIR/backend/.env" 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"
    echo "  - .env CORS_ORIGINS_LIST: $(grep '^CORS_ORIGINS_LIST=' "$APP_DIR/backend/.env" 2>/dev/null | cut -d'=' -f2 || echo 'Not set')"
    echo
}

# Main execution
main() {
    clear
    echo "=========================================="
    echo "StudyQnA Assistant - Installation Script"
    echo "=========================================="
    echo
    
    check_root
    check_ubuntu
    get_user_input
    
    update_system
    install_essentials
    create_app_user
    setup_firewall
    setup_swap
    install_postgresql
    install_python
    install_nodejs
    setup_backend
    setup_frontend
    setup_nginx
    create_systemd_service
    setup_ssl
    create_env_template
    
    print_summary
}

# Run main function
main

