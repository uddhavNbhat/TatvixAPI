@echo off
setlocal EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
set "MISSING_COUNT=0"

title Tatvix Project Setup

echo ==================================================
echo               TATVIX PUBLIC SETUP
echo ==================================================
echo.
echo This script will:
echo   1) Build Docker image: file_service_API
echo   2) Build Docker image(s): Gemma_Inference_API
echo   3) Install Python requirements: TatvIX_API
echo   4) Install npm packages: TatvixFrontend
echo.

echo ---------------- Prerequisites ----------------
echo Required:
echo   - Python ^> 3.10
echo   - Docker Desktop
echo   - Docker Compose plugin
echo   - MongoDB (Compass/community)
echo   - SQLite
echo   - Node.js ^> 20
echo.

call :check_python
call :check_node
call :check_docker
call :check_docker_compose
call :check_mongodb
call :check_sqlite

echo.
if %MISSING_COUNT% GTR 0 (
	echo [WARN] %MISSING_COUNT% prerequisite check^(s^) are missing or not verified.
	echo        Setup may fail until you install/configure the missing tools.
) else (
	echo [OK] All prerequisite checks passed.
)
echo.

set /p CONFIRM="Type YES to begin setup (or anything else to cancel): "
if /I not "%CONFIRM%"=="YES" (
	echo Setup cancelled.
	exit /b 0
)

echo.
echo ==================================================
echo Starting setup...
echo ==================================================

call :step_prompt "Step 1/4 - Build Docker image for file_service_API"
call :build_file_service
if errorlevel 1 goto :SETUP_FAILED

call :step_prompt "Step 2/4 - Build Docker image(s) for Gemma_Inference_API"
call :build_gemma
if errorlevel 1 goto :SETUP_FAILED

call :step_prompt "Step 3/4 - Install Python requirements for TatvIX_API"
call :install_tatvix_api_requirements
if errorlevel 1 goto :SETUP_FAILED

call :step_prompt "Step 4/4 - Install npm packages for TatvixFrontend"
call :install_frontend_packages
if errorlevel 1 goto :SETUP_FAILED

echo.
echo ==================================================
echo Setup completed successfully.
echo ==================================================
exit /b 0

:SETUP_FAILED
echo.
echo ==================================================
echo Setup failed. Fix the above error and rerun setup.bat.
echo ==================================================
exit /b 1

:step_prompt
echo.
echo --------------------------------------------------
echo %~1
echo --------------------------------------------------
pause
exit /b 0

:check_python
set "PY_OK=0"
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
if not defined PY_VER (
	echo [MISSING] Python not found in PATH.
	set /a MISSING_COUNT+=1
	exit /b 0
)
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
	set "PY_MAJOR=%%a"
	set "PY_MINOR=%%b"
)
if !PY_MAJOR! GTR 3 set "PY_OK=1"
if !PY_MAJOR! EQU 3 if !PY_MINOR! GEQ 10 set "PY_OK=1"

if !PY_OK! EQU 1 (
	echo [OK] Python %PY_VER%
) else (
	echo [MISSING] Python %PY_VER% detected. Need Python 3.10+.
	set /a MISSING_COUNT+=1
)

where pip >nul 2>&1
if errorlevel 1 (
	echo [MISSING] pip not found in PATH.
	set /a MISSING_COUNT+=1
) else (
	echo [OK] pip available
)
exit /b 0

:check_node
set "NODE_OK=0"
for /f "tokens=1 delims=v" %%v in ('node --version 2^>^&1') do set "NODE_RAW=%%v"
if not defined NODE_RAW (
	for /f "tokens=*" %%v in ('node --version 2^>^&1') do set "NODE_VER=%%v"
) else (
	set "NODE_VER=v%NODE_RAW%"
)

if not defined NODE_VER (
	echo [MISSING] Node.js not found in PATH.
	set /a MISSING_COUNT+=1
	exit /b 0
)

set "NODE_VER=%NODE_VER:v=%"
for /f "tokens=1 delims=." %%a in ("%NODE_VER%") do set "NODE_MAJOR=%%a"
if !NODE_MAJOR! GEQ 20 set "NODE_OK=1"

if !NODE_OK! EQU 1 (
	echo [OK] Node.js v%NODE_VER%
) else (
	echo [MISSING] Node.js v%NODE_VER% detected. Need Node.js 20+.
	set /a MISSING_COUNT+=1
)

where npm >nul 2>&1
if errorlevel 1 (
	echo [MISSING] npm not found in PATH.
	set /a MISSING_COUNT+=1
) else (
	echo [OK] npm available
)
exit /b 0

:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
	echo [MISSING] Docker not found or not running.
	set /a MISSING_COUNT+=1
) else (
	echo [OK] Docker available
)
exit /b 0

:check_docker_compose
docker compose version >nul 2>&1
if errorlevel 1 (
	echo [MISSING] Docker Compose plugin not available.
	set /a MISSING_COUNT+=1
) else (
	echo [OK] Docker Compose available
)
exit /b 0

:check_mongodb
where mongod >nul 2>&1
if errorlevel 1 (
	where mongosh >nul 2>&1
	if errorlevel 1 (
		echo [MISSING] MongoDB CLI not found in PATH. Install MongoDB/Compass.
		set /a MISSING_COUNT+=1
	) else (
		echo [OK] MongoDB shell available
	)
) else (
	echo [OK] MongoDB server binary available
)
exit /b 0

:check_sqlite
where sqlite3 >nul 2>&1
if errorlevel 1 (
	echo [MISSING] sqlite3 not found in PATH.
	set /a MISSING_COUNT+=1
) else (
	echo [OK] sqlite3 available
)
exit /b 0

:build_file_service
pushd "%ROOT_DIR%file_service_API" || (
	echo [ERROR] Could not open file_service_API directory.
	exit /b 1
)
docker build -t storage_service_api .
if errorlevel 1 (
	popd
	echo [ERROR] Docker build failed for file_service_API.
	exit /b 1
)
popd
echo [OK] file_service_API image built.
exit /b 0

:build_gemma
pushd "%ROOT_DIR%Gemma_Inference_API" || (
	echo [ERROR] Could not open Gemma_Inference_API directory.
	exit /b 1
)
docker compose build
if errorlevel 1 (
	popd
	echo [ERROR] Docker compose build failed for Gemma_Inference_API.
	exit /b 1
)
popd
echo [OK] Gemma_Inference_API image(s) built.
exit /b 0

:install_tatvix_api_requirements
pushd "%ROOT_DIR%TatvIX_API" || (
	echo [ERROR] Could not open TatvIX_API directory.
	exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
	echo Creating virtual environment in TatvIX_API\.venv ...
	python -m venv .venv
	if errorlevel 1 (
		popd
		echo [ERROR] Failed to create Python virtual environment.
		exit /b 1
	)
)

call .venv\Scripts\activate
if errorlevel 1 (
	popd
	echo [ERROR] Failed to activate TatvIX_API virtual environment.
	exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
	call deactivate >nul 2>&1
	popd
	echo [ERROR] Failed to upgrade pip.
	exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
	call deactivate >nul 2>&1
	popd
	echo [ERROR] Failed to install TatvIX_API requirements.
	exit /b 1
)

call deactivate >nul 2>&1
popd
echo [OK] TatvIX_API requirements installed.
exit /b 0