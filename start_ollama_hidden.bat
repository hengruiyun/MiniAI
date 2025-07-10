@echo off
rem Start Ollama service with hidden window
rem Author: 267278466@qq.com

%SystemDrive%
CD %USERPROFILE%\AppData\Local\Programs\Ollama

rem Start ollama serve with hidden window
MiniOllama.exe  -start

echo Ollama service started successfully
timeout /t 2 /nobreak >nul 