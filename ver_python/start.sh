#!/usr/bin/env bash
# TeamSchedule (Python/FastAPI) 서버 시작 스크립트
#
# 사용법: ./start.sh
#   - 최초 실행 시 .venv 가상환경을 만들고 requirements.txt 를 설치한다.
#   - systemd 사용자 서비스(ssa-schedule.service)가 등록된 서버에서는 그 서비스를 시작한다.
#   - 그 외 환경에서는 uvicorn 을 백그라운드로 실행한다. (로그: server.log, PID: server.pid)
#   - 바인딩 주소 변경: HOST=0.0.0.0 PORT=8080 ./start.sh  (백그라운드 실행일 때만 적용)
set -euo pipefail
cd "$(dirname "$0")"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8766}"
SERVICE="${SERVICE:-ssa-schedule.service}"
PID_FILE=server.pid
LOG_FILE=server.log

# 1. 가상환경 준비 (requirements.txt 가 바뀌었으면 다시 설치)
if [ ! -x .venv/bin/python ]; then
    echo "가상환경 생성 중..."
    python3 -m venv .venv
fi
if [ ! -f .venv/.installed ] || [ requirements.txt -nt .venv/.installed ]; then
    echo "패키지 설치 중..."
    .venv/bin/pip install -q --upgrade pip
    .venv/bin/pip install -q -r requirements.txt
    touch .venv/.installed
fi

# 2. systemd 서비스가 있으면 서비스로 실행
if command -v systemctl >/dev/null 2>&1 && systemctl --user cat "$SERVICE" >/dev/null 2>&1; then
    systemctl --user start "$SERVICE"
    echo "서버 시작됨 (systemd: $SERVICE)"
    exit 0
fi

# 3. 없으면 백그라운드 프로세스로 실행
if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "이미 실행 중입니다 (PID $(cat "$PID_FILE"))"
    exit 0
fi

nohup .venv/bin/uvicorn main:app --host "$HOST" --port "$PORT" \
    --proxy-headers --forwarded-allow-ips 127.0.0.1 >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

sleep 2
if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "서버 시작됨: http://$HOST:$PORT (PID $(cat "$PID_FILE"), 로그: $LOG_FILE)"
else
    echo "서버 시작 실패. 로그:"
    tail -n 20 "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
