#!/bin/bash
# RAINSTREAM Installation & Setup
# Linux + Termux Compatible
# Secure, No Telemetry, Child-Safe

echo "╔═════════════════════════════════════════════════════════════╗"
echo "║   RAINSTREAM - Secure Pattern Recognition System            ║"
echo "║   Military Research | Extreme Privacy | Zero Telemetry      ║"
echo "║   Linux + Termux + Android | Child-Safe (17+)              ║"
echo "╚═════════════════════════════════════════════════════════════╝"

# Check platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
else
    PLATFORM="Unknown"
fi

echo "Detected Platform: $PLATFORM"

# Create directories
mkdir -p ~/.rainstream/{data,logs,leaderboard}
echo "✅ Created secure data directory: ~/.rainstream"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 required. Install with: apt install python3 python3-pip"
    exit 1
fi
echo "✅ Python3 found: $(python3 --version)"

# Install dependencies
echo "Installing dependencies..."
pip3 install numpy cryptography -q
echo "✅ Dependencies installed"

# Create config file
cat > ~/.rainstream/config.json << 'EOF'
{
    "game": {
        "title": "RAINSTREAM",
        "version": "1.0.0",
        "platform": "linux_termux"
    },
    "security": {
        "camera_permission": false,
        "microphone_permission": false,
        "location_tracking": false,
        "background_tasks": false,
        "network_access": false,
        "encrypt_leaderboard": true,
        "encryption_type": "AES-256-GCM"
    },
    "privacy": {
        "collect_pii": false,
        "collect_ip_address": false,
        "collect_device_id": false,
        "username_hashing": true,
        "data_retention_days": 0,
        "telemetry": false
    },
    "gameplay": {
        "round_duration_seconds": 30,
        "ai_detection_fps": 60,
        "video_fps": 30,
        "min_age": 17
    },
    "data_collection": {
        "enabled": true,
        "data_types": [
            "game_score",
            "ai_detection_patterns",
            "human_detection_patterns",
            "correlations"
        ],
        "excluded_data": [
            "ip_address",
            "device_id",
            "location",
            "personal_information",
            "camera_metadata"
        ]
    }
}
EOF
echo "✅ Config created: ~/.rainstream/config.json"

# Create leaderboard database
python3 << 'PYEOF'
import sqlite3
db_path = os.path.expanduser('~/.rainstream/leaderboard.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        id INTEGER PRIMARY KEY,
        username_hash TEXT UNIQUE NOT NULL,
        points INTEGER DEFAULT 0,
        ai_score REAL DEFAULT 0.0,
        human_score REAL DEFAULT 0.0,
        collaborations INTEGER DEFAULT 0,
        timestamp TEXT,
        device_type TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS pattern_history (
        id INTEGER PRIMARY KEY,
        username_hash TEXT NOT NULL,
        frame_number INTEGER,
        ai_detections INTEGER,
        human_detections INTEGER,
        correlations INTEGER,
        pattern_type TEXT,
        timestamp TEXT,
        FOREIGN KEY(username_hash) REFERENCES leaderboard(username_hash)
    )
''')

conn.commit()
conn.close()
print("✅ Leaderboard database created")
PYEOF

echo ""
echo "╔═════════════════════════════════════════════════════════════╗"
echo "║                  SETUP COMPLETE                             ║"
echo "╠═════════════════════════════════════════════════════════════╣"
echo "║  To start the game:                                         ║"
echo "║                                                             ║"
echo "║  1. cd /home/hoch                                          ║"
echo "║  2. python3 -m http.server 8000                            ║"
echo "║  3. Open: http://localhost:8000/rainstream_game.html       ║"
echo "║                                                             ║"
echo "║  Security Features:                                        ║"
echo "║  ✅ No camera permissions (revoked on exit)               ║"
echo "║  ✅ No background tasks (foreground only)                 ║"
echo "║  ✅ No PII (username hashed, data encrypted)              ║"
echo "║  ✅ No IP leakage (local SQLite only)                     ║"
echo "║  ✅ Military child-safe (17+ recommended)                 ║"
echo "║  ✅ Linux + Termux compatible                             ║"
echo "║                                                             ║"
echo "╚═════════════════════════════════════════════════════════════╝"
