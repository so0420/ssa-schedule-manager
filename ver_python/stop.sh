#!/usr/bin/env bash
# TeamSchedule (Python/FastAPI) 서버 종료 스크립트
#
# 사용법: ./stop.sh
#   - systemd 사용자 서비스(ssa-schedule.service)가 등록된 서버에서는 그 서비스를 멈춘다.
#   - 그 외 환경에서는 start.sh 가 남긴 server.pid 의 프로세스를 종료한다.
set -euo pipefail
cd "$(dirname "$0")"

SERVICE="${SERVICE:-ssa-schedule.service}"
PID_FILE=server.pid

# 1. systemd 서비스가 있으면 서비스 종료
if command -v systemctl >/dev/null 2>&1 && systemctl --user cat "$SERVICE" >/dev/null 2>&1; then
    systemctl --user stop "$SERVICE"
    echo "서버 종료됨 (systemd: $SERVICE)"
    exit 0
fi

# 2. 없으면 PID 파일로 종료
if [ ! -f "$PID_FILE" ] || ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "실행 중인 서버가 없습니다."
    rm -f "$PID_FILE"
    exit 0
fi

PID="$(cat "$PID_FILE")"
kill "$PID"
for _ in $(seq 1 10); do
    kill -0 "$PID" 2>/dev/null || break
    sleep 1
done
if kill -0 "$PID" 2>/dev/null; then
    echo "정상 종료되지 않아 강제 종료합니다."
    kill -9 "$PID"
fi
rm -f "$PID_FILE"
echo "서버 종료됨 (PID $PID)"
