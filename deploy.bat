@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "ACTION=%~1"
if "%ACTION%"=="" set "ACTION=up"

if /I "%ACTION%"=="help" goto :help
if /I "%ACTION%"=="status" goto :status
if /I "%ACTION%"=="logs" goto :logs
if /I "%ACTION%"=="stop" goto :stop
if /I "%ACTION%"=="restart" goto :restart
if /I not "%ACTION%"=="up" goto :unknown_action

:check_docker
where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker was not found. Install and start Docker Desktop first.
  exit /b 1
)

docker compose version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Compose v2 is not available.
  exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Cannot connect to Docker. Start Docker Desktop and retry.
  exit /b 1
)

if not exist ".env" (
  if not exist ".env.example" (
    echo [ERROR] .env.example was not found.
    exit /b 1
  )
  copy /Y ".env.example" ".env" >nul
  echo [INFO] Created .env from .env.example.
  echo [INFO] Add API keys to .env before using AI generation.
)

echo [1/4] Validating Docker Compose configuration...
docker compose config --quiet
if errorlevel 1 (
  echo [ERROR] Compose validation failed. Check .env and docker-compose.yml.
  exit /b 1
)

echo [2/4] Building images and starting services...
docker compose up -d --build --remove-orphans
if errorlevel 1 (
  echo [ERROR] Build or startup failed. Run deploy.bat logs for details.
  exit /b 1
)

echo [3/4] Waiting for the health endpoint...
call :read_port
set /a HEALTH_TRY=0

:health_loop
set /a HEALTH_TRY+=1
call :health_check
if not errorlevel 1 goto :healthy
if !HEALTH_TRY! GEQ 60 goto :health_timeout
timeout /t 2 /nobreak >nul
goto :health_loop

:healthy
echo [4/4] Deployment completed.
docker compose ps
echo.
echo Application:  http://localhost:!APP_PORT!
echo API docs:     http://localhost:!APP_PORT!/docs
echo Health check: http://localhost:!APP_PORT!/health
echo.
echo After editing .env, run: deploy.bat restart
if "%~1"=="" pause
exit /b 0

:health_timeout
echo [WARN] Containers started, but health check failed for 120 seconds.
docker compose ps
echo Run deploy.bat logs for details.
if "%~1"=="" pause
exit /b 1

:restart
call :check_docker_runtime
if errorlevel 1 exit /b 1
if not exist ".env" (
  if not exist ".env.example" (
    echo [ERROR] .env.example was not found.
    exit /b 1
  )
  copy /Y ".env.example" ".env" >nul
)
echo Rebuilding and recreating containers with the latest .env...
docker compose up -d --build --force-recreate --remove-orphans
if errorlevel 1 exit /b 1
docker compose ps
echo Restart completed.
exit /b 0

:status
call :check_docker_runtime
if errorlevel 1 exit /b 1
docker compose ps
exit /b %ERRORLEVEL%

:logs
call :check_docker_runtime
if errorlevel 1 exit /b 1
echo Press Ctrl+C to stop following logs.
docker compose logs -f --tail=200
exit /b %ERRORLEVEL%

:stop
call :check_docker_runtime
if errorlevel 1 exit /b 1
echo Stopping services. Named volumes and user data will be retained.
docker compose down
exit /b %ERRORLEVEL%

:check_docker_runtime
where docker >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker was not found.
  exit /b 1
)
docker info >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker is not running.
  exit /b 1
)
docker compose version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Docker Compose v2 is not available.
  exit /b 1
)
exit /b 0

:read_port
set "APP_PORT=8080"
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /I "%%A"=="APP_PORT" set "APP_PORT=%%B"
  )
)
if "!APP_PORT!"=="" set "APP_PORT=8080"
exit /b 0

:health_check
where curl.exe >nul 2>&1
if not errorlevel 1 (
  curl.exe -fsS "http://127.0.0.1:!APP_PORT!/health" >nul 2>&1
  exit /b !ERRORLEVEL!
)
powershell.exe -NoProfile -Command "try { $response = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 'http://127.0.0.1:!APP_PORT!/health'; if ($response.StatusCode -eq 200) { exit 0 }; exit 1 } catch { exit 1 }" >nul 2>&1
exit /b !ERRORLEVEL!

:unknown_action
echo [ERROR] Unknown command: %ACTION%
goto :help

:help
echo Usage: deploy.bat [up^|restart^|status^|logs^|stop^|help]
echo.
echo   up       Build and start the project. This is the default action.
echo   restart  Rebuild and recreate containers using the latest .env.
echo   status   Show container status.
echo   logs     Follow the latest 200 log lines.
echo   stop     Stop services and retain named volumes.
echo   help     Show this help message.
exit /b 0
