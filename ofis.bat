@echo off
rem Komuta Üssü'nü açar (başlatıcı exe yoksa). Önce LM Studio ya da Bionic açık olmalı ve yerel
rem sunucusu (Local Server / Local Model API) çalışmalı.
cd /d "%~dp0"
set "PYW=pythonw"
if exist python-yolu.txt set /p PYW=<python-yolu.txt
start "" "%PYW%" -X utf8 ofis.py
timeout /t 2 >nul
start "" http://127.0.0.1:8765
