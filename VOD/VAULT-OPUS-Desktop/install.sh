#!/bin/bash
set -euo pipefail

# ----------------------------------------------------------------------
# VAULT_OPUS - LINUX INSTALLER (REQUIRES ROOT)
# ----------------------------------------------------------------------
LOG_FILE="/tmp/vault_opus_install.log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Colour control (respect NO_COLOR)
if [[ -z "${NO_COLOR:-}" ]]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'
    CYAN='\033[0;36m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
else
    RED=''; GREEN=''; BLUE=''; CYAN=''; YELLOW=''; BOLD=''; NC=''
fi

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success(){ echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning(){ echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error()  { echo -e "${RED}[ERROR]${NC} $1"; }
die()        { log_error "$1"; exit 1; }

# ----------------------------------------------------------------------
# ROOT CHECK – MUST BE ROOT
# ----------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}${BOLD}[ERROR] This installer must be run as root.${NC}"
    echo -e "${YELLOW}Please re-run with: sudo $0${NC}"
    exit 1
fi
log_success "Running with root privileges."

# ----------------------------------------------------------------------
# Parse command line arguments
# ----------------------------------------------------------------------
SKIP_NODE=0
SKIP_FRONTEND=0
AUTO_INSTALL=0
UNINSTALL=0
HELP=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-node) SKIP_NODE=1 ;;
        --skip-frontend) SKIP_FRONTEND=1 ;;
        --auto-install) AUTO_INSTALL=1 ;;
        --uninstall) UNINSTALL=1 ;;
        --help) HELP=1 ;;
        *) log_warning "Unknown option: $1" ;;
    esac
    shift
done

if [[ $HELP -eq 1 ]]; then
    cat <<EOF
Usage: sudo $0 [options]

Options:
  --skip-node        Skip Node.js installation even if missing
  --skip-frontend    Skip npm install for frontend directories
  --auto-install     Automatically answer Yes to all prompts
  --uninstall        Remove venv, node_modules, and config backups
  --help             Show this help

Example: sudo $0 --auto-install --skip-frontend
EOF
    exit 0
fi

if [[ $UNINSTALL -eq 1 ]]; then
    echo -e "${BOLD}Uninstalling VAULT_OPUS...${NC}"
    [[ -d venv ]] && rm -rf venv && log_info "Removed venv"
    [[ -d src/WI/client/node_modules ]] && rm -rf src/WI/client/node_modules
    [[ -d src/WI/mobile/node_modules ]] && rm -rf src/WI/mobile/node_modules
    rm -f src/config.json.bak.* 2>/dev/null
    log_success "Uninstall complete."
    exit 0
fi

# ----------------------------------------------------------------------
# Banner
# ----------------------------------------------------------------------
clear
echo -e "${CYAN}${BOLD}"
echo " __      __    _    _   _ _   _______    ____   _____  _    _  _____ "
echo " \ \    / /   / \  | | | | | |__   __|  / __ \ |  __ \| |  | |/ ____|"
echo "  \ \  / /   / _ \ | | | | |    | |    | |  | || |__) | |  | | (___  "
echo "   \ \/ /   / ___ \| | | | |    | |    | |  | ||  ___/| |  | |\___ \ "
echo "    \  /   / /   \ \ |_| | |____| |    | |__| || |    | |__| |____) |"
echo "     \/   /_/     \_\____|______|_|     \____/ |_|     \____/|_____/ "
echo -e "${NC}"
echo -e "${BLUE}${BOLD}>>> THE INFINITY CLOUD STORAGE PROJECT <<< ${NC}\n"

# ----------------------------------------------------------------------
# 1. Python 3.8+ bootstrap (multi‑distro)
# ----------------------------------------------------------------------
log_info "Checking Python 3.8+..."
if ! command -v python3 &>/dev/null; then
    log_warning "Python3 not found."
    if [[ $AUTO_INSTALL -eq 0 ]]; then
        read -p "Install Python3 and pip? (y/n): " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && die "Python3 is required."
    fi
    # Detect package manager (root already, so no sudo needed)
    if command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y python3 python3-pip python3-venv
    elif command -v dnf &>/dev/null; then
        dnf install -y python3 python3-pip
    elif command -v yum &>/dev/null; then
        yum install -y python3 python3-pip
    elif command -v pacman &>/dev/null; then
        pacman -S --noconfirm python python-pip
    elif command -v zypper &>/dev/null; then
        zypper install -y python3 python3-pip
    else
        die "No supported package manager. Please install Python 3.8+ manually."
    fi
fi

# Verify version
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" || die "Python 3.8+ required."
log_success "Python $(python3 --version) ready."

# ----------------------------------------------------------------------
# 2. Node.js bootstrap (optional, still root)
# ----------------------------------------------------------------------
HAS_NODE=0
if [[ $SKIP_NODE -eq 1 ]]; then
    log_warning "Node.js installation skipped by user."
else
    log_info "Checking Node.js & npm..."
    if ! command -v node &>/dev/null || ! command -v npm &>/dev/null; then
        log_warning "Node.js/npm missing."
        if [[ $AUTO_INSTALL -eq 0 ]]; then
            read -p "Install Node.js LTS? (y/n): " -n 1 -r
            echo
            [[ $REPLY =~ ^[Yy]$ ]] || { log_warning "Frontend will be disabled."; SKIP_FRONTEND=1; HAS_NODE=0; }
        fi
        if [[ $SKIP_FRONTEND -eq 0 ]]; then
            # Use nodesource if possible
            if command -v curl &>/dev/null; then
                curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
                apt-get install -y nodejs
            else
                # Fallback to distro package
                if command -v apt-get &>/dev/null; then
                    apt-get install -y nodejs npm
                elif command -v dnf &>/dev/null; then
                    dnf install -y nodejs npm
                elif command -v pacman &>/dev/null; then
                    pacman -S --noconfirm nodejs npm
                else
                    log_error "Cannot install Node.js automatically. Please install manually."
                    SKIP_FRONTEND=1
                fi
            fi
        fi
    fi
    if command -v node &>/dev/null && command -v npm &>/dev/null; then
        HAS_NODE=1
        log_success "Node.js $(node -v) / npm $(npm -v) ready."
    fi
fi

# ----------------------------------------------------------------------
# 3. Virtual environment & Python dependencies (with retries)
# ----------------------------------------------------------------------
log_info "Creating virtual environment..."
if [[ ! -d venv ]]; then
    python3 -m venv venv || die "Failed to create venv (install python3-venv)."
fi
source venv/bin/activate
log_success "Virtual environment activated."

if [[ ! -f requirements.txt ]]; then
    die "requirements.txt not found."
fi

log_info "Installing Python packages (retry up to 3 times)..."
for attempt in {1..3}; do
    if pip install --no-cache-dir -r requirements.txt; then
        log_success "Python dependencies installed."
        break
    else
        log_warning "Attempt $attempt failed. Retrying in 3 seconds..."
        sleep 3
        if [[ $attempt -eq 3 ]]; then
            die "pip install failed after 3 attempts."
        fi
    fi
done

# ----------------------------------------------------------------------
# 4. Discord configuration (backup + jq/python fallback)
# ----------------------------------------------------------------------
mkdir -p src
CONFIG_FILE="src/config.json"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo '{"discord": {"token": "", "channel_id": "", "command_prefix": "/"}}' > "$CONFIG_FILE"
else
    # backup with timestamp
    cp "$CONFIG_FILE" "src/config.json.bak.$(date +%Y%m%d-%H%M%S)"
fi

echo -e "\n${BOLD}--- Discord Bot Configuration ---${NC}"
if [[ $AUTO_INSTALL -eq 0 ]]; then
    read -p "Discord Bot Token (leave empty to keep): " TOKEN
    read -p "Discord Channel ID (leave empty to keep): " CHANNEL_ID
else
    TOKEN=""
    CHANNEL_ID=""
fi

# strip quotes and commas
TOKEN=$(echo "$TOKEN" | sed 's/[",]//g')
CHANNEL_ID=$(echo "$CHANNEL_ID" | sed 's/[",]//g')

# Use jq if available, else python
if command -v jq &>/dev/null; then
    [[ -n "$TOKEN" ]] && jq --arg t "$TOKEN" '.discord.token = $t' "$CONFIG_FILE" > config.tmp && mv config.tmp "$CONFIG_FILE"
    [[ -n "$CHANNEL_ID" ]] && jq --arg c "$CHANNEL_ID" '.discord.channel_id = $c' "$CONFIG_FILE" > config.tmp && mv config.tmp "$CONFIG_FILE"
else
    python3 - <<EOF
import json
with open('$CONFIG_FILE', 'r') as f:
    d = json.load(f)
if '$TOKEN':
    d['discord']['token'] = '$TOKEN'
if '$CHANNEL_ID':
    d['discord']['channel_id'] = '$CHANNEL_ID'
with open('$CONFIG_FILE', 'w') as f:
    json.dump(d, f, indent=2)
EOF
fi
log_success "Configuration updated."

# ----------------------------------------------------------------------
# 5. Frontend npm packages (optional)
# ----------------------------------------------------------------------
if [[ $SKIP_FRONTEND -eq 1 ]]; then
    log_warning "Frontend npm install skipped by user."
elif [[ $HAS_NODE -eq 0 ]]; then
    log_warning "Node.js not available – skipping frontend setup."
else
    echo -e "\n${BOLD}--- Frontend Setup ---${NC}"
    if [[ $AUTO_INSTALL -eq 0 ]]; then
        read -p "Install npm packages for Web & Mobile? (y/n): " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && { log_info "Skipping frontend."; exit 0; }
    fi
    for dir in "src/WI/client" "src/WI/mobile"; do
        if [[ -f "$dir/package.json" ]]; then
            log_info "Running npm install in $dir ..."
            (cd "$dir" && npm install) || log_warning "npm install failed in $dir"
        else
            log_warning "No package.json in $dir – skipping."
        fi
    done
    log_success "Frontend setup completed."
fi

# ----------------------------------------------------------------------
# Final instructions
# ----------------------------------------------------------------------
echo -e "\n${GREEN}${BOLD}VAULT_OPUS Installation Complete!${NC}"
echo "Log file: $LOG_FILE"
echo
echo "Run the app with:"
echo "  - CLI:          source venv/bin/activate && python src/VAULT_OPUS.py"
echo "  - GUI backend:  source venv/bin/activate && python src/WI/server.py"
echo "  - Desktop GUI:  cd src/WI/client && npm run dev"
echo "  - Android GUI:  cd src/WI/mobile && npm run android"
echo -e "\n${CYAN}Enjoy!${NC}\n"