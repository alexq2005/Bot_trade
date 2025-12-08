# ⚠️ ADVERTENCIA - Modo LIVE en Test Bot

## 🚨 IMPORTANTE

El **Test Bot** ahora soporta **modo LIVE** (dinero real) además de Paper Trading.

---

## ⚠️ Cuándo Usar Modo LIVE en Test Bot

### ✅ SÍ usar LIVE cuando:

1. **Ya probaste exhaustivamente en Paper Trading**
   - Mínimo 24-48 horas en paper
   - Sin errores en logs
   - Resultados consistentes

2. **Quieres validar cambios menores en producción**
   - Cambios en thresholds
   - Ajustes de configuración
   - Nuevos mensajes de Telegram

3. **Necesitas probar con dinero real pero con capital limitado**
   - Usar pocos símbolos (2-3)
   - Configurar límites más estrictos
   - Monitoreo activo

### ❌ NO usar LIVE cuando:

1. **Cambios importantes en el código**
   - Modificaciones en `execute_trade()`
   - Cambios en lógica de señales
   - Nuevos algoritmos no probados

2. **Features experimentales**
   - Código nuevo sin validar
   - Lógica compleja no probada
   - Integraciones nuevas

3. **No estás seguro**
   - Si tienes dudas, usa Paper Trading
   - Mejor prevenir que lamentar

---

## 🛡️ Protecciones en Modo LIVE

### ✅ Protecciones Implementadas:

1. **Confirmación Doble**
   - Primera confirmación al seleccionar modo
   - Segunda confirmación antes de iniciar
   - Debes escribir exactamente "EJECUTAR LIVE"

2. **PID Separado**
   - Test bot usa `test_bot_pid.txt`
   - No sobrescribe `bot.pid` de producción
   - Evita conflictos

3. **Límites de Riesgo**
   - Usa `test_bot/configs/testing_config.json`
   - Límites más conservadores que producción
   - Max posición: 5% (vs 14% en producción)
   - Max trades diarios: 3 (vs 8 en producción)
   - Max pérdida diaria: 2% (vs 5% en producción)

4. **Símbolos Controlados**
   - Por defecto solo 3 símbolos
   - Puedes seleccionar manualmente
   - Evita sobre-exposición

---

## 📋 Checklist Antes de Usar LIVE

Antes de ejecutar test bot en modo LIVE:

```
□ Probado en Paper Trading mínimo 24 horas
□ Sin errores en logs de paper trading
□ Resultados de paper trading son buenos
□ Entiendo todos los cambios que hice
□ Límites de riesgo configurados correctamente
□ Símbolos seleccionados cuidadosamente
□ Backup del estado estable creado
□ Monitoreo activo disponible (logs, dashboard)
□ Bot de producción detenido (para evitar conflictos)
□ Tengo plan de acción si algo sale mal
```

---

## 🔄 Workflow Recomendado

### Para Cambios Pequeños:

```
1. Modificar en test_bot/
2. Probar en Paper Trading (24h)
3. Si OK: Probar en LIVE con 1-2 símbolos
4. Monitorear activamente (2-4 horas)
5. Si OK: Copiar a producción
```

### Para Cambios Grandes:

```
1. Modificar en test_bot/
2. Probar en Paper Trading (48-72h)
3. Validar resultados exhaustivamente
4. NO usar LIVE en test bot
5. Copiar directamente a producción
6. Monitorear producción activamente
```

---

## 🚨 Qué Hacer si Algo Sale Mal

### Si el Test Bot en LIVE tiene problemas:

1. **Detener Inmediatamente**
   ```powershell
   # Encontrar PID
   Get-Content test_bot\test_bot_pid.txt
   
   # Matar proceso
   taskkill /F /PID [PID]
   ```

2. **Verificar Operaciones en IOL**
   - Acceder a InvertirOnline
   - Revisar operaciones ejecutadas
   - Cerrar posiciones si es necesario

3. **Revisar Logs**
   ```powershell
   Get-Content logs\*.log -Tail 100
   ```

4. **Restaurar Backup si es necesario**
   ```powershell
   python restaurar_backup.py stable_20251202_114451_pre_test_bot_estructura
   ```

---

## ⚙️ Configuración Recomendada para LIVE Testing

### En `test_bot/configs/testing_config.json`:

```json
{
  "paper_trading": false,
  "risk_per_trade": 0.005,        // 0.5% (muy conservador)
  "max_position_size_pct": 3,     // 3% máximo por posición
  "max_daily_trades": 2,          // Solo 2 trades al día
  "max_daily_loss_pct": 1.0,      // Detener si pierde 1%
  
  "buy_threshold": 35,            // Más exigente (vs 25)
  "sell_threshold": -35,          // Más exigente (vs -25)
  "min_confidence": "HIGH",       // Solo alta confianza
  
  "analysis_interval_minutes": 60 // Igual que producción
}
```

---

## 💡 Mejores Prácticas

### Antes de LIVE:
1. ✅ Probar en paper mínimo 24-48h
2. ✅ Validar que no hay errores
3. ✅ Configurar límites conservadores
4. ✅ Seleccionar pocos símbolos (2-3)
5. ✅ Detener bot de producción (evitar conflictos)

### Durante LIVE:
1. ✅ Monitorear logs en tiempo real
2. ✅ Revisar cada operación ejecutada
3. ✅ Tener dashboard abierto
4. ✅ Estar disponible para intervenir
5. ✅ Límite de tiempo (2-4 horas máximo)

### Después de LIVE:
1. ✅ Revisar todas las operaciones
2. ✅ Calcular P&L real
3. ✅ Analizar logs completos
4. ✅ Decidir si copiar a producción
5. ✅ Documentar resultados en CHANGELOG.md

---

## 🎯 Resumen

- ✅ **Paper Trading**: Para desarrollo y testing general
- ✅ **LIVE Trading**: Solo para validación final antes de producción
- ⚠️  **Siempre** con confirmación doble y límites conservadores
- 🛡️  **Protecciones** múltiples para evitar pérdidas

**Regla de Oro**: Si tienes dudas, usa Paper Trading ✅

---

Desarrollado por: Antigravity + Claude
Fecha: 2025-12-02

