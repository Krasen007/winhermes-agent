@echo off
REM ============================================================================
REM Hermes Agent Setup Script for Windows
REM ============================================================================
REM Quick setup for developers on native Windows (not WSL).
REM Uses uv for fast Python provisioning and package management.
REM
REM Prerequisites:
REM   - Git for Windows (provides bash.exe for terminal tool)
REM   - Python 3.11+ (uv can install it automatically)
REM
REM Usage:
REM   setup-hermes.bat
REM
REM This script:
REM  1. Installs uv if not present
REM  2. Creates a virtual environment with Python 3.11 via uv
REM  3. Installs all dependencies (main package + submodules)
REM  4. Creates .env from template (if not exists)
REM  5. Creates hermes.cmd in a PATH-accessible location
REM  6. Runs the setup wizard (optional)
REM ============================================================================

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "PYTHON_VERSION=3.11"

echo.
echo ============================================
echo   Hermes Agent Setup (Windows)
echo ============================================
echo.

REM ============================================================================
REM Check for Git Bash
REM ============================================================================

echo [1/7] Checking for Git Bash...

set "BASH_EXE="
if exist "%ProgramFiles%\Git\bin\bash.exe" (
    set "BASH_EXE=%ProgramFiles%\Git\bin\bash.exe"
) else if exist "%ProgramFiles(x86)%\Git\bin\bash.exe" (
    set "BASH_EXE=%ProgramFiles(x86)%\Git\bin\bash.exe"
) else if exist "%LOCALAPPDATA%\Programs\Git\bin\bash.exe" (
    set "BASH_EXE=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
) else (
    where bash.exe >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%i in ('where bash.exe') do set "BASH_EXE=%%i"
    )
)

if defined BASH_EXE (
    echo   [OK] Git Bash found: %BASH_EXE%
) else (
    echo   [!!] Git Bash not found!
    echo   Hermes requires Git for Windows for terminal commands.
    echo   Download from: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

REM ============================================================================
REM Install / locate uv
REM ============================================================================

echo [2/7] Checking for uv...

set "UV_CMD="
where uv.exe >nul 2>&1
if %errorlevel% equ 0 (
    set "UV_CMD=uv"
    goto :uv_found
)

if exist "%USERPROFILE%\.local\uv.exe" (
    set "UV_CMD=%USERPROFILE%\.local\uv.exe"
    goto :uv_found
)

if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
    set "UV_CMD=%USERPROFILE%\.cargo\bin\uv.exe"
    goto :uv_found
)

echo   Installing uv...
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1

if exist "%USERPROFILE%\.local\uv.exe" (
    set "UV_CMD=%USERPROFILE%\.local\uv.exe"
) else if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
    set "UV_CMD=%USERPROFILE%\.cargo\bin\uv.exe"
) else (
    echo   [!!] Failed to install uv. Visit https://docs.astral.sh/uv/
    pause
    exit /b 1
)

:uv_found
for /f "tokens=*" %%v in ('%UV_CMD% --version 2^>nul') do set "UV_VER=%%v"
echo   [OK] uv found (%UV_VER%)

REM ============================================================================
REM Python check
REM ============================================================================

echo [3/7] Checking Python %PYTHON_VERSION%...

%UV_CMD% python find %PYTHON_VERSION% >nul 2>&1
if %errorlevel% neq 0 (
    echo   Installing Python %PYTHON_VERSION% via uv...
    %UV_CMD% python install %PYTHON_VERSION%
)

for /f "tokens=*" %%v in ('%UV_CMD% python find %PYTHON_VERSION% 2^>nul') do set "PYTHON_PATH=%%v"
echo   [OK] Python ready

REM ============================================================================
REM Virtual environment
REM ============================================================================

echo [4/7] Setting up virtual environment...

if exist venv (
    echo   Removing old venv...
    rmdir /s /q venv 2>nul
)

%UV_CMD% venv venv --python %PYTHON_VERSION%
echo   [OK] venv created

REM ============================================================================
REM Dependencies
REM ============================================================================

echo [5/7] Installing dependencies (this may take a few minutes)...

set "VIRTUAL_ENV=%SCRIPT_DIR%venv"

%UV_CMD% pip install -e ".[all]" >nul 2>&1
if %errorlevel% neq 0 (
    %UV_CMD% pip install -e "."
)

echo   [OK] Dependencies installed

REM ============================================================================
REM Submodules
REM ============================================================================

echo   Installing submodules...

if exist mini-swe-agent\pyproject.toml (
    %UV_CMD% pip install -e ".\mini-swe-agent" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] mini-swe-agent installed
    ) else (
        echo   [!!] mini-swe-agent install failed (terminal tools may not work)
    )
) else (
    echo   [!!] mini-swe-agent not found (run: git submodule update --init --recursive)
)

if exist tinker-atropos\pyproject.toml (
    %UV_CMD% pip install -e ".\tinker-atropos" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] tinker-atropos installed
    ) else (
        echo   [!!] tinker-atropos install failed (RL tools may not work)
    )
) else (
    echo   [!!] tinker-atropos not found (run: git submodule update --init --recursive)
)

REM ============================================================================
REM Environment file
REM ============================================================================

echo [6/7] Setting up environment file...

if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo   [OK] Created .env from template
    ) else (
        echo   [!!] No .env.example found
    )
) else (
    echo   [OK] .env exists
)

REM ============================================================================
REM Create hermes.cmd entry point
REM ============================================================================

echo [7/7] Creating hermes command...

set "BIN_DIR=%USERPROFILE%\.local\bin"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

REM Create hermes.cmd launcher
(
echo @echo off
echo set "HERMES_HOME_DIR=%USERPROFILE%\.hermes"
echo set "HERMES_GIT_BASH_PATH=%BASH_EXE%"
echo "%SCRIPT_DIR%venv\Scripts\hermes.exe" %%*
) > "%BIN_DIR%\hermes.cmd"

echo   [OK] Created %BIN_DIR%\hermes.cmd

REM Check if bin dir is on PATH
echo %PATH% | findstr /i /c:"%BIN_DIR%" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [!!] %BIN_DIR% is not on your PATH.
    echo   Add it manually, or run this in an elevated PowerShell:
    echo.
    echo     [Environment]::SetEnvironmentVariable("Path", $env:Path + ";%BIN_DIR%", "User")
    echo.
    echo   Then restart your terminal.
)

REM ============================================================================
REM Seed bundled skills
REM ============================================================================

echo.
echo Syncing bundled skills to %USERPROFILE%\.hermes\skills\...

set "HERMES_SKILLS_DIR=%USERPROFILE%\.hermes\skills"
if not exist "%HERMES_SKILLS_DIR%" mkdir "%HERMES_SKILLS_DIR%"

"%SCRIPT_DIR%venv\Scripts\python.exe" "%SCRIPT_DIR%tools\skills_sync.py" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Skills synced
) else (
    if exist skills\ (
        xcopy /s /q /y skills\* "%HERMES_SKILLS_DIR%\" >nul 2>&1
        echo   [OK] Skills copied
    )
)

REM ============================================================================
REM Done
REM ============================================================================

echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo Next steps:
echo.
echo   1. Configure API keys:
echo      hermes setup
echo.
echo   2. Start chatting:
echo      hermes
echo.
echo Other commands:
echo   hermes status          # Check configuration
echo   hermes doctor          # Diagnose issues
echo.

set /p "RUN_WIZARD=Would you like to run the setup wizard now? [Y/n] "
if /i "!RUN_WIZARD!" neq "n" (
    echo.
    "%SCRIPT_DIR%venv\Scripts\python.exe" -m hermes_cli.main setup
)

echo.
pause
