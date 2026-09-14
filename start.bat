@echo off
REM ClinicCare — Start All Services (Windows)
REM Run this from the healthcare-app\ directory

REM ── Set Node.js on PATH (handles both common install locations) ──────────
IF EXIST "C:\Program Files\nodejs\node.exe" (
  SET "NODE_DIR=C:\Program Files\nodejs"
) ELSE IF EXIST "%APPDATA%\nvm\current\node.exe" (
  SET "NODE_DIR=%APPDATA%\nvm\current"
) ELSE (
  REM fallback — try USERPROFILE\nodejs (nvm-windows default)
  SET "NODE_DIR=%USERPROFILE%\AppData\Roaming\nvm\current"
)
SET "PATH=%NODE_DIR%;%PATH%"

echo =======================================
echo   ClinicCare Healthcare App Startup
echo   Node: %NODE_DIR%
echo =======================================
echo.

REM Verify node is available
"%NODE_DIR%\node.exe" --version >nul 2>&1
IF ERRORLEVEL 1 (
  echo ERROR: Node.js not found. Please install Node.js 18+ and re-run.
  pause
  exit /b 1
)

echo Starting ML Service on :5001 ...
start "ClinicCare ML-Service" cmd /k "cd /d %~dp0ml-service && python app.py"

timeout /t 2 /nobreak >nul

echo Starting Backend API on :4000 ...
start "ClinicCare Backend" cmd /k "cd /d %~dp0backend && SET PATH=%NODE_DIR%;%PATH% && node src/index.js"

timeout /t 3 /nobreak >nul

echo Starting Frontend on :5173 ...
start "ClinicCare Frontend" cmd /k "cd /d %~dp0frontend && SET PATH=%NODE_DIR%;%PATH% && npm run dev"

echo.
echo =======================================
echo   All services starting in separate windows.
echo.
echo   Frontend:   http://localhost:5173
echo   Backend:    http://localhost:4000
echo   ML Service: http://localhost:5001
echo.
echo   Demo logins:
echo   Admin:   admin@clinic.com   / Admin@123
echo   Doctor:  dr.adams@clinic.com / Doctor@123
echo   Patient: alice@example.com  / Patient@123
echo =======================================
echo.
pause
