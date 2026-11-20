#!/usr/bin/env bash
# TeamSchedule (Java/Spring Boot) 서버 실행 스크립트
#
# 사용법: ./run.sh
#   - Gradle Wrapper로 빌드한 뒤 서버를 포그라운드로 실행한다. (종료: Ctrl+C)
#   - JDK 17 이상이 필요하다.
#   - 포트 변경: PORT=9090 ./run.sh  (기본값 8080)
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8080}"

if ! command -v java >/dev/null 2>&1 && [ -z "${JAVA_HOME:-}" ]; then
    echo "Java를 찾을 수 없습니다. JDK 17 이상을 설치하거나 JAVA_HOME을 설정하세요."
    exit 1
fi

echo "서버 시작: http://localhost:$PORT  (종료: Ctrl+C)"
exec sh ./gradlew bootRun --args="--server.port=$PORT"
