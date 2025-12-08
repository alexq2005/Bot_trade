# Script para verificar conflictos del bot
# Verifica si hay múltiples instancias corriendo

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🔍 VERIFICACIÓN DE CONFLICTOS DEL BOT" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar archivo PID
Write-Host "📋 Archivos de Control:" -ForegroundColor Yellow
if (Test-Path "bot.pid") {
    $pidContent = Get-Content "bot.pid" -ErrorAction SilentlyContinue
    if ($pidContent) {
        $pidValue = [int]$pidContent
        Write-Host "   ✅ bot.pid existe (PID: $pidValue)" -ForegroundColor Green
        
        # Verificar si el proceso existe
        $proc = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "   ✅ Proceso activo: $($proc.ProcessName)" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Proceso NO existe (PID obsoleto)" -ForegroundColor Yellow
            Write-Host "   💡 Considera eliminar bot.pid" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️  bot.pid existe pero está vacío" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ bot.pid no existe" -ForegroundColor Red
}

# Verificar stop_flag
if (Test-Path "stop_flag.txt") {
    Write-Host "   ⚠️  stop_flag.txt existe (bot está siendo detenido)" -ForegroundColor Yellow
} else {
    Write-Host "   ✅ stop_flag.txt no existe" -ForegroundColor Green
}

Write-Host ""

# Verificar procesos Python relacionados
Write-Host "🐍 Procesos Python relacionados:" -ForegroundColor Yellow
$pythonProcs = Get-Process python* -ErrorAction SilentlyContinue

if ($pythonProcs) {
    $botProcs = @()
    foreach ($proc in $pythonProcs) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -and ($cmdLine -like "*run_bot*" -or $cmdLine -like "*trading_bot*" -or $cmdLine -like "*test2_bot_trade*")) {
                $botProcs += [PSCustomObject]@{
                    PID = $proc.Id
                    Name = $proc.ProcessName
                    CommandLine = $cmdLine
                }
            }
        } catch {
            # Si no se puede obtener CommandLine, continuar
        }
    }
    
    if ($botProcs.Count -gt 0) {
        Write-Host "   ⚠️  Se encontraron $($botProcs.Count) proceso(s) del bot:" -ForegroundColor Yellow
        $botProcs | Format-Table -AutoSize
        
        if ($botProcs.Count -gt 1) {
            Write-Host "   🚨 CONFLICTO: Múltiples instancias del bot corriendo" -ForegroundColor Red
            Write-Host "   💡 Detén todas las instancias antes de iniciar otra" -ForegroundColor Yellow
        } else {
            Write-Host "   ✅ Solo una instancia del bot corriendo" -ForegroundColor Green
        }
    } else {
        Write-Host "   ✅ No se encontraron procesos del bot" -ForegroundColor Green
    }
} else {
    Write-Host "   ✅ No hay procesos Python activos" -ForegroundColor Green
}

Write-Host ""

# Verificar errores 409 en logs
Write-Host "📄 Verificando logs de Telegram (errores 409):" -ForegroundColor Yellow
$logFiles = Get-ChildItem "logs\trading_bot_*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($logFiles) {
    $conflictos = Select-String -Path $logFiles.FullName -Pattern "409|Conflict|conflicto" -ErrorAction SilentlyContinue | Select-Object -Last 5
    
    if ($conflictos) {
        Write-Host "   ⚠️  Se encontraron errores 409 en los logs:" -ForegroundColor Yellow
        foreach ($conflicto in $conflictos) {
            Write-Host "      $($conflicto.Line.Trim())" -ForegroundColor Gray
        }
        Write-Host "   💡 Esto indica conflicto de Telegram Polling" -ForegroundColor Yellow
    } else {
        Write-Host "   ✅ No se encontraron errores 409 en los logs recientes" -ForegroundColor Green
    }
} else {
    Write-Host "   ℹ️  No se encontraron archivos de log" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "💡 RECOMENDACIONES" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Si solo hay UNA instancia:" -ForegroundColor Green
Write-Host "   • Puedes continuar normalmente" -ForegroundColor White
Write-Host "   • El bot maneja conflictos automáticamente" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Si hay MÚLTIPLES instancias:" -ForegroundColor Yellow
Write-Host "   1. Detén todas: /detener_bot (desde Telegram)" -ForegroundColor White
Write-Host "   2. O crea stop_flag.txt" -ForegroundColor White
Write-Host "   3. Espera a que se detengan" -ForegroundColor White
Write-Host "   4. Inicia solo UNA instancia" -ForegroundColor White
Write-Host ""
Write-Host "📄 Ver documentación: CONFLICTOS_MONITOREO_CONTINUO.md" -ForegroundColor Cyan

