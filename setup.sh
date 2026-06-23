#!/usr/bin/env bash
set -e

# Simple spinner that runs while a background command is alive
spin() {
    local pid=$!
    local delay=0.1
    local spinstr='|/-\\'
    while kill -0 "$pid" 2>/dev/null; do
        local tmp=${spinstr#?}
        printf "\r[%c] " "$spinstr"
        spinstr=$tmp${spinstr%"$tmp"}
        sleep $delay
    done
    printf "\r    \r"
}

echo "=== Setting up GridLock Command Center (Linux/macOS) ==="

# 1️⃣ Create Python virtual environment
echo -n "1️⃣ Creating Python virtual environment... "
python3 -m venv venv & spin
echo "✅"

# Activate the environment for subsequent commands
source venv/bin/activate

# 2️⃣ Install Python dependencies
echo -n "2️⃣ Installing Python dependencies... "
pip install -r requirements.txt > /dev/null 2>&1 & spin
echo "✅"

# 3️⃣ Install Node.js dependencies
echo -n "3️⃣ Installing Node.js dependencies... "
( cd frontend && npm install > /dev/null 2>&1 ) & spin
echo "✅"

echo "--------------------------------------------------------"
echo "✅ Setup complete! You can now run the app with ./run.sh"
echo "--------------------------------------------------------"

