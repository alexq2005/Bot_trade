# Script para activar el entorno virtual en PowerShell
# Ejecuta: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
# Luego: .\activar_venv.ps1

# Cambiar política de ejecución solo para esta sesión
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

# Activar entorno virtual
& "$PSScriptRoot\..\..\.venv\Scripts\Activate.ps1"

Write-Host "✅ Entorno virtual activado" -ForegroundColor Green

