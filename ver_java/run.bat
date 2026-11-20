@echo off
rem TeamSchedule (Java/Spring Boot) 서버 실행 스크립트
rem
rem 사용법: run.bat  (또는 탐색기에서 더블클릭)
rem   - Gradle Wrapper로 빌드한 뒤 서버를 실행한다. (종료: Ctrl+C)
rem   - JDK 17 이상이 필요하다.
rem   - 포트 변경: set PORT=9090 후 run.bat  (기본값 8080)
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if "%PORT%"=="" set PORT=8080

where java >nul 2>nul
if errorlevel 1 if "%JAVA_HOME%"=="" (
    echo Java를 찾을 수 없습니다. JDK 17 이상을 설치하거나 JAVA_HOME을 설정하세요.
    pause
    exit /b 1
)

echo 서버 시작: http://localhost:%PORT%  (종료: Ctrl+C)
call "%~dp0gradlew.bat" bootRun --args="--server.port=%PORT%"
set EXITCODE=%ERRORLEVEL%
if not "%EXITCODE%"=="0" pause
exit /b %EXITCODE%
