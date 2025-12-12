@echo off
REM Script para cargar datos históricos
cd /d "%~dp0"

REM Activar entorno virtual y ejecutar script
call ..\..\.venv\Scripts\activate.bat
python cargar_datos_historicos.py

pause

