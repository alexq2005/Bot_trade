# 📊 Guía de Monitoreo de 14 Días - Test Bot

## 🎯 Objetivo

Monitorear el **test_bot con 13 estrategias avanzadas** durante 14 días para:
- Medir mejora real en win rate y retornos
- Validar que las estrategias funcionan en condiciones reales
- Decidir si aplicar a producción

---

## 📅 Período de Monitoreo

**Inicio:** Diciembre 3, 2025  
**Fin:** Diciembre 17, 2025  
**Duración:** 14 días continuos

---

## 🔧 Componentes del Sistema

### 1. Monitor Automático (`monitor_14_dias.py`)

**Qué hace:**
- Monitorea el bot 24/7
- Verifica que esté ejecutándose
- Recopila estadísticas diarias
- Genera reportes a las 18:00
- Envía alertas si el bot se detiene
- Compara con baseline

**Corre en background continuamente**

### 2. Bot de Test (`run_bot.py`)

**Configuración:**
- Modo: Paper Trading
- Estrategias: 13 avanzadas activas
- Intervalo: 60 minutos
- Portfolio: COMPLETO (IOL + Tienda Broker)

**Debe estar ejecutándose durante los 14 días**

### 3. Script de Progreso (`ver_progreso_14dias.py`)

**Qué hace:**
- Muestra progreso actual (X/14 días)
- Métricas acumuladas
- Comparación con baseline
- Reportes diarios históricos

**Ejecutar cuando quieras ver el progreso**

---

## 🚀 Cómo Iniciar

### Opción 1: Batch Script (Recomendado)

```bash
cd test_bot
iniciar_monitoreo_14dias.bat
```

Esto inicia el monitor en una ventana separada.

### Opción 2: Manual

```bash
cd test_bot
python monitor_14_dias.py
```

---

## 📊 Qué se Monitorea

### Métricas Diarias:

**Operaciones:**
- Total trades del día
- Compras vs Ventas
- Trades ganadores vs perdedores
- P&L del día

**Análisis:**
- Total análisis realizados
- Señales generadas (BUY/SELL/HOLD)
- Score promedio

**Estrategias:**
- Cuáles se ejecutaron
- Cuáles contribuyeron más al score

---

## 📱 Notificaciones por Telegram

### Mensaje de Inicio:
```
🚀 INICIO DE MONITOREO DE 14 DÍAS
📅 Fecha inicio: 2025-12-03
📅 Fecha fin: 2025-12-17
🧬 Estrategias Activas: 13
```

### Reporte Diario (18:00):
```
📊 REPORTE DÍA X/14
⚡ Operaciones: X
💰 P&L del día: $X
📊 Win Rate: X%
🎯 Señales: BUY X, SELL X, HOLD X
```

### Alertas:
```
⚠️ ALERTA
El bot de test está DETENIDO
```

### Reporte Final (Día 14):
```
🎉 REPORTE FINAL - 14 DÍAS
📊 Win Rate: X% (+Y% vs baseline)
💰 Retorno: X% (+Y% vs baseline)
🎯 DECISIÓN: APLICAR/CONSIDERAR/NO_APLICAR
```

---

## 📈 Baseline (Valores de Referencia)

**Bot actual sin estrategias avanzadas:**
- Win Rate: 50%
- Retorno Mensual: 7.5%
- Max Drawdown: 12.5%

**Objetivo con estrategias:**
- Win Rate: 75%+ (+25%)
- Retorno Mensual: 15-25% (+10-15%)
- Max Drawdown: 3-5% (-7-10%)

---

## 🎯 Criterios de Decisión

### ✅ APLICAR A PRODUCCIÓN:
- Win Rate mejora ≥10% O
- Retorno mejora ≥5%

### ⚠️ CONSIDERAR:
- Win Rate mejora 5-10% O
- Retorno mejora 2-5%
- → Evaluar más, extender monitoreo

### ❌ NO APLICAR:
- Win Rate mejora <5% O
- Retorno empeora
- → Ajustar estrategias, no aplicar

---

## 🔍 Verificar Progreso

### En Cualquier Momento:

```bash
cd test_bot
python ver_progreso_14dias.py
```

**Muestra:**
- Días transcurridos
- Barra de progreso visual
- Métricas acumuladas
- Comparación con baseline
- Todos los reportes diarios

---

## 📁 Archivos Generados

### `data/monitoring_14dias.json`

Contiene:
```json
{
  "start_date": "2025-12-03T...",
  "end_date": "2025-12-17T...",
  "daily_reports": [
    {
      "date": "2025-12-03",
      "trades": {"total": 5, "pnl": 150, ...},
      "analyses": 26,
      ...
    }
  ],
  "total_trades": 50,
  "total_analyses": 300,
  "initial_capital": 21891.65,
  "current_capital": 22500.00
}
```

---

## ⚙️ Configuración

### Horarios:
- **Reporte diario:** 18:00 horas
- **Check de status:** Cada hora
- **Alertas:** Inmediatas si bot se detiene

### Modificar horario de reporte:

Edita `monitor_14_dias.py`, línea ~140:
```python
if current_time.hour == 18 and current_time.minute < 5:  # ← Cambiar hora aquí
```

---

## 🛠️ Troubleshooting

### Si el bot se detiene:

El monitor enviará alerta por Telegram.

**Reiniciar:**
```bash
cd test_bot
python run_bot.py --paper --continuous
```

El monitoreo continuará automáticamente.

### Si quieres detener el monitoreo:

- Presiona `Ctrl+C` en la ventana del monitor
- O cierra la ventana

**Nota:** Podrás reanudar después, los datos persisten en `monitoring_14dias.json`

---

## 📊 Qué Esperar

### Días 1-3:
- El bot se adapta al mercado
- Pocas operaciones
- Win rate puede variar

### Días 4-7:
- Más operaciones
- Patrones se empiezan a ver
- Win rate se estabiliza

### Días 8-14:
- Suficiente muestra estadística
- Win rate confiable
- Decisión clara

**Mínimo recomendado:** 30-50 trades para validación estadística

---

## 🎯 Después de 14 Días

### Reporte Final Incluirá:

1. **Métricas totales**
   - Total trades
   - Win rate final
   - P&L total
   - Retorno %

2. **Comparación con baseline**
   - Mejora en win rate
   - Mejora en retorno
   - Mejora en drawdown

3. **Recomendación automática**
   - APLICAR: Si mejora >10%
   - CONSIDERAR: Si mejora 5-10%
   - NO_APLICAR: Si mejora <5%

4. **Análisis por estrategia** (si implementado)
   - Cuáles aportaron más
   - Cuáles no funcionaron
   - Ajustes recomendados

---

## 📞 Contacto y Soporte

**Monitoreo vía Telegram:**
- Reportes diarios automáticos
- Alertas en tiempo real
- Reporte final al completar

**Comandos útiles:**
- `/status` - Estado del bot
- `/portfolio` - Ver portafolio
- `/pnl` - P&L actual

---

## ✅ Checklist

- [x] 13 estrategias implementadas
- [x] Test unitario pasado (13/13)
- [x] Bot de test ejecutándose
- [x] Monitor de 14 días activo
- [ ] Día 1 completado
- [ ] Día 7 completado
- [ ] Día 14 completado
- [ ] Reporte final generado
- [ ] Decisión tomada

---

**Fecha de inicio:** 3 de Diciembre, 2025  
**Fecha de finalización esperada:** 17 de Diciembre, 2025  

**¡Buena suerte en el monitoreo!** 🚀💰

