# Script para activar el entorno virtual sin problemas de política
# Uso: .\activar_venv.ps1

# Método 1: Intentar cambiar política temporalmente (solo para esta sesión)
try {
    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
    & .\venv\Scripts\Activate.ps1
    Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
    Write-Host "💡 Usa 'deactivate' para desactivar" -ForegroundColor Yellow
} catch {
    Write-Host "⚠️  No se pudo activar con el método estándar" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📋 SOLUCIÓN ALTERNATIVA:" -ForegroundColor Cyan
    Write-Host "   Usa directamente el Python del venv:" -ForegroundColor White
    Write-Host "   .\venv\Scripts\python.exe [tu_script.py]" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Ejemplo:" -ForegroundColor White
    Write-Host "   .\venv\Scripts\python.exe run_bot.py --live --continuous" -ForegroundColor Green
}

