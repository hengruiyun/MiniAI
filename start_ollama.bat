@echo off
rem Start Ollama service with hidden window
rem Author: 267278466@qq.com

%SystemDrive%
CD %USERPROFILE%\AppData\Local\Programs\Ollama

rem Start ollama serve with hidden window
powershell -WindowStyle Hidden -Command "Start-Process 'ollama.exe' -ArgumentList 'serve' -WindowStyle Hidden"

echo Ollama service started successfully
timeout /t 2 /nobreak >nul 