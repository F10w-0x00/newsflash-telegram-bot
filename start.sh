#!/bin/sh

# ==============================================================================
# NewsFlash Telegram Bot - POSIX Process Manager (Linux / FreeBSD)
# ==============================================================================

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$BASE_DIR/venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

PID=$(pgrep -f "python.*rss_bot.py")

if [ -z "$PID" ]; then
    nohup "$PYTHON_BIN" "$BASE_DIR/rss_bot.py" > "$BASE_DIR/run.log" 2>&1 &
    sleep 2
    NEW_PID=$(pgrep -f "python.*rss_bot.py")
    if [ -n "$NEW_PID" ]; then
        echo "$(date): RSS Bot started successfully (PID: $NEW_PID)" >> "$BASE_DIR/watchdog.log"
        echo "RSS Bot started successfully with PID: $NEW_PID"
    else
        echo "Failed to start RSS Bot. Please check $BASE_DIR/run.log for details."
        cat "$BASE_DIR/run.log"
        exit 1
    fi
else
    echo "RSS Bot is already running with PID: $PID"
fi
