@echo off
setlocal enabledelayedexpansion

:: ------------------------------
:: MAIN MENU
:: ------------------------------
:MENU
cls
echo ========================================
echo        SYSTEM STARTUP MENU
echo ========================================
echo.
echo 1. Start Gemma Inference (Docker)
echo 2. Start File Service API (Docker)
echo 3. Start TatvIX API (Uvicorn)
echo 4. Start MCP Server (Uvicorn)
echo 5. Stop Gemma Inference (Docker)
echo 6. Stop File Service API (Docker)
echo 7. Stop TatvIX API + MCP Server
echo 8. Exit
echo.
set /p choice="Enter your choice: "

if "%choice%"=="1" goto START_GEMMA
if "%choice%"=="2" goto START_FILE_SERVICE
if "%choice%"=="3" goto START_TATVIX_API
if "%choice%"=="4" goto START_MCP
if "%choice%"=="5" goto STOP_GEMMA
if "%choice%"=="6" goto STOP_FILE_SERVICE
if "%choice%"=="7" goto STOP_APP_SERVERS
if "%choice%"=="8" goto EXIT

goto MENU


:START_GEMMA
echo Starting Weaviate + Transformers...
cd /d Gemma_Inference_API

:: ===== Check model folder =====
if exist models (
    echo Models folder already exists. Skipping download.
) else (
    echo Models folder not found. Running model_script.py...
    python model_script.py
    if !errorlevel! neq 0 (
        echo model_script.py failed!
        cd..
        pause
        goto MENU
    )
)

echo Starting docker compose...
docker compose up -d

cd ..
pause
goto MENU


:START_FILE_SERVICE
echo Starting File Service API container...
cd /d file_service_API
docker build -t storage_service_api .
if !errorlevel! neq 0 (
    echo Docker build failed for file service.
    cd ..
    pause
    goto MENU
)
docker rm -f storage_service_api >nul 2>&1
docker run -d --name storage_service_api -p 8007:8007 -v file_service_storage:/storage storage_service_api
if !errorlevel! neq 0 (
    echo Failed to start file service container.
    cd ..
    pause
    goto MENU
)
cd ..
pause
goto MENU


:START_TATVIX_API
echo Starting TatvIX API server...
start "TatvIX API" cmd /k "cd /d TatvIX_API && if exist .venv\Scripts\activate call .venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
pause
goto MENU

:START_MCP
echo Starting MCP server...
start "MCP Server" cmd /k "if exist McpServer\.venv\Scripts\activate call McpServer\.venv\Scripts\activate && uvicorn McpServer.server:mcp.http_app --factory --host 0.0.0.0 --port 5050 --reload"
pause
goto MENU

:STOP_GEMMA
echo Stopping Weaviate + Transformers...
cd /d Gemma_Inference_API
docker compose down
cd ..
pause
goto MENU

:STOP_FILE_SERVICE
echo Stopping File Service API container...
docker rm -f storage_service_api >nul 2>&1
echo File service container stopped.
pause
goto MENU

:STOP_APP_SERVERS
echo Stopping TatvIX API and MCP Server...

taskkill /FI "WINDOWTITLE eq TatvIX API*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq MCP Server*" /T /F >nul 2>&1

echo TatvIX API and MCP server stopped.
pause
goto MENU

:EXIT
echo Exiting...
pause
exit /b
