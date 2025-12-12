@echo off
REM Script para detener TODOS los procesos del bot y monitor

title Detener Todo - Test Bot
cd /d "%~dp0"

echo ============================================================
echo DETENIENDO TODOS LOS COMPONENTES
echo ============================================================
echo.

REM Detener bot si existe PID
if exist bot.pid (
    echo [1/2] Deteniendo Bot...
    for /f %%i in (bot.pid) do (
        echo PID encontrado: %%i
        taskkill /F /PID %%i >nul 2>&1
        if errorlevel 1 (
            echo Bot ya estaba detenido
        ) else (
            echo Bot detenido correctamente
        )
    )
    del bot.pid >nul 2>&1
) else (
    echo [1/2] Bot: No hay PID (ya detenido o nunca iniciado)
)

echo.

REM Detener procesos Python relacionados
echo [2/2] Deteniendo procesos Python relacionados...
taskkill /F /FI "WINDOWTITLE eq Bot Test*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Monitor 14 Dias*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Dashboard Test*" >nul 2>&1

REM También buscar por nombre de proceso
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /I "PID"') do (
    echo Verificando proceso Python PID: %%i
)

echo.
echo ============================================================
echo PROCESOS DETENIDOS
echo ============================================================
echo.
echo Si algun proceso sigue corriendo, cierralo manualmente desde
echo el Administrador de Tareas (Ctrl+Shift+Esc)
echo.
pause



