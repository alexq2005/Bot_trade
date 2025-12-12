# 🧠 SISTEMA DE AUTOPROGRAMACIÓN - test2_bot_trade

## ⚠️ ADVERTENCIA IMPORTANTE

**Este bot puede ahora razonar y modificarse a sí mismo.**

El sistema de autoprogramación permite al bot:
- Analizar su propio performance
- Razonar sobre mejoras necesarias
- Generar y aplicar código mejorado
- Modificar su propio comportamiento

**Esto conlleva riesgos significativos. Úsalo bajo tu propia responsabilidad.**

---

## 🎯 COMPONENTES IMPLEMENTADOS

### 1. **SelfProgrammingEngine** (`src/services/self_programming_engine.py`)

Motor principal de autoprogramación que:

- **Analiza Performance:**
  - Win rate, profit factor, drawdown
  - Identifica problemas y oportunidades
  - Analiza logs de errores

- **Razona sobre Mejoras:**
  - Identifica áreas de mejora
  - Prioriza cambios según impacto
  - Genera recomendaciones específicas

- **Genera Código:**
  - Modifica umbrales de trading
  - Ajusta stop loss y take profit
  - Optimiza tamaño de posición

- **Aplica Cambios Seguros:**
  - Crea backups automáticos
  - Valida sintaxis antes de aplicar
  - Permite rollback si algo falla

### 2. **ReasoningSystem** (`src/services/reasoning_system.py`)

Sistema de razonamiento autónomo que:

- **Razona sobre Trades:**
  - Evalúa si ejecutar un trade
  - Considera historial del símbolo
  - Analiza condiciones de mercado
  - Puede sobrescribir señales si razonamiento es negativo

- **Razona sobre Estrategias:**
  - Evalúa efectividad de cada estrategia
  - Recomienda ajustar pesos
  - Identifica estrategias problemáticas

- **Razona sobre Auto-mejora:**
  - Identifica áreas de mejora
  - Prioriza cambios necesarios
  - Sugiere mejoras específicas

---

## 🔄 CICLO DE AUTOPROGRAMACIÓN

El bot ejecuta un ciclo de automejora cada:

- **48 horas** (automático)
- **100 trades** (basado en actividad)

### Proceso:

1. **Análisis de Performance**
   - Analiza trades recientes
   - Calcula métricas clave
   - Identifica problemas

2. **Razonamiento**
   - Evalúa qué mejoras son necesarias
   - Prioriza según impacto
   - Genera recomendaciones

3. **Generación de Código**
   - Genera código mejorado
   - Valida sintaxis
   - Prepara cambios

4. **Aplicación Segura**
   - Crea backup
   - Aplica cambio
   - Valida resultado

5. **Registro**
   - Guarda en historial
   - Notifica por Telegram
   - Permite rollback si es necesario

---

## 🛡️ SALVAGUARDAS IMPLEMENTADAS

### Archivos Protegidos

Los siguientes archivos **NO** pueden ser modificados:

- `run_bot.py` - Punto de entrada principal
- `professional_config.json` - Configuración crítica
- `requirements.txt` - Dependencias

### Validaciones

- ✅ Validación de sintaxis antes de aplicar
- ✅ Backups automáticos antes de cada cambio
- ✅ Rollback automático si hay errores
- ✅ Límite de cambios por ciclo (máx 3)

### Historial

- Todos los cambios se registran en:
  - `data/self_programming_history.json`
  - `backups/self_programming/` (backups de archivos)

---

## 📊 TIPOS DE MEJORAS QUE PUEDE APLICAR

### 1. Ajuste de Umbrales

**Problema detectado:** Win rate bajo (<50%)

**Mejora:** Aumenta `buy_threshold` en 5 puntos

**Ejemplo:**
```python
# Antes
buy_threshold = 20

# Después (si win rate < 50%)
buy_threshold = 25
```

### 2. Ajuste de Stop Loss

**Problema detectado:** Pérdidas promedio > ganancias promedio

**Mejora:** Reduce multiplicador ATR para stop loss más ajustado

**Ejemplo:**
```python
# Antes
stop_loss = price - 2.5 * atr

# Después (si pérdidas > ganancias)
stop_loss = price - 2.0 * atr
```

### 3. Optimización de Tamaño de Posición

**Oportunidad detectada:** Win rate alto (>60%) y ganancias positivas

**Mejora:** Aumenta tamaño de posición ligeramente

**Ejemplo:**
```python
# Antes
position_size = capital * 0.05

# Después (si performance positivo)
position_size = capital * 0.055
```

---

## 🔍 MONITOREO

### Ver Historial de Cambios

```bash
cat data/self_programming_history.json
```

### Ver Backups

```bash
ls backups/self_programming/
```

### Ver Razonamientos

```bash
cat data/reasoning_history.json
```

---

## ⚠️ RIESGOS Y CONSIDERACIONES

### Riesgos

1. **Código Incorrecto:**
   - El bot puede generar código con errores
   - Aunque se valida sintaxis, puede haber errores lógicos

2. **Cambios No Deseados:**
   - Puede modificar comportamiento de forma inesperada
   - Puede optimizar para condiciones específicas que luego cambian

3. **Sobre-optimización:**
   - Puede ajustar parámetros demasiado específicos
   - Puede perder generalidad

4. **Bugs en el Sistema:**
   - El sistema de autoprogramación puede tener bugs
   - Puede aplicar cambios incorrectos

### Recomendaciones

1. **Monitoreo Activo:**
   - Revisa cambios aplicados regularmente
   - Verifica que el bot siga funcionando correctamente

2. **Backups Manuales:**
   - Haz backups manuales antes de cambios importantes
   - Guarda versiones estables

3. **Testing:**
   - Prueba en paper trading primero
   - Valida cambios antes de usar en producción

4. **Rollback:**
   - Si algo sale mal, usa el sistema de rollback
   - Restaura desde backups si es necesario

---

## 🚀 USO

El sistema se activa automáticamente en modo continuo.

### Ejecutar Ciclo Manual

```python
from src.services.self_programming_engine import SelfProgrammingEngine

engine = SelfProgrammingEngine()
result = engine.run_improvement_cycle()
```

### Ver Razonamiento de un Trade

El razonamiento se ejecuta automáticamente para cada trade.

Los razonamientos se guardan en `data/reasoning_history.json`.

---

## 📝 EJEMPLO DE CAMBIO APLICADO

```json
{
  "timestamp": "2025-12-06T23:30:00",
  "improvement": {
    "type": "adjust_thresholds",
    "description": "Aumentar umbral de compra para mejorar win rate",
    "target_file": "trading_bot.py",
    "action": "increase_buy_threshold",
    "reasoning": "Win rate actual 45.2% es bajo. Aumentar umbral de compra puede mejorar calidad de trades."
  },
  "backup_path": "backups/self_programming/trading_bot_20251206_233000.py",
  "file": "trading_bot.py",
  "status": "applied"
}
```

---

## 🔄 ROLLBACK

Si necesitas revertir un cambio:

```python
from src.services.self_programming_engine import SelfProgrammingEngine
import json

engine = SelfProgrammingEngine()

# Cargar historial
with open('data/self_programming_history.json', 'r') as f:
    history = json.load(f)

# Revertir último cambio
if history:
    last_change = history[-1]
    engine.rollback_change(last_change)
    print("✅ Cambio revertido")
```

---

## 🎯 CONCLUSIÓN

El bot ahora tiene capacidad de:

- ✅ Razonar sobre sus decisiones
- ✅ Analizar su propio performance
- ✅ Identificar problemas
- ✅ Generar mejoras
- ✅ Aplicar cambios de forma segura
- ✅ Aprender de sus errores

**Pero recuerda:**
- ⚠️ Monitorea los cambios
- ⚠️ Valida que todo funcione
- ⚠️ Ten backups
- ⚠️ Usa con precaución

---

**El bot ahora puede razonar y mejorarse a sí mismo. ¡Úsalo responsablemente!** 🧠🤖

