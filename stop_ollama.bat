@echo off
rem Stop Ollama service by terminating process
rem Author: 267278466@qq.com

echo Stopping Ollama service...

rem Kill ollama.exe process
taskkill /f /im ollama.exe >nul 2>&1

rem Check if process was terminated
tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
if %errorlevel% equ 0 (
    echo Failed to stop Ollama service
    pause
    exit /b 1
) else (
    echo Ollama service stopped successfully
)

timeout /t 2 /nobreak >nul 