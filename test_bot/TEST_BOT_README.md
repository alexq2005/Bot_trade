# 🧪 Test Bot - Copia Completa del Sistema

**Fecha de Creación**: 2 de Diciembre, 2025  
**Propósito**: Área de desarrollo y testing completamente independiente  
**Estado**: ✅ Operativa  

---

## 📦 Contenido de test_bot/

Esta carpeta contiene una **COPIA COMPLETA** del sistema IOL Quantum AI que puedes modificar libremente sin afectar el bot de producción.

### 🗂️ Estructura Copiada:

```
test_bot/
├── 📄 ARCHIVOS PRINCIPALES (Copias para modificar)
│   ├── trading_bot.py              # Copia del motor principal (159KB) ✅
│   ├── dashboard.py                # Copia del dashboard (247KB) ✅
│   ├── run_bot.py                  # Copia del launcher ✅
│   ├── cli.py                      # Copia del CLI ✅
│   ├── .env                        # Copia de credenciales ✅
│   ├── requirements.txt            # Dependencias ✅
│   ├── test_trading_bot.py         # Script de prueba interactivo ✅
│   └── test_sistema_completo.py    # Test del sistema completo ✅
│
├── 📂 configs/ (Configuraciones de Testing)
│   ├── professional_config.json    # Config principal (copia) ✅
│   ├── my_portfolio.json           # Portafolio (copia) ✅
│   └── testing_config.json         # Config específica de testing ✅
│
├── 📂 src/ (CÓDIGO FUENTE COMPLETO - Copia para modificar)
│   ├── connectors/                 # Todos los conectores ✅
│   │   ├── iol_client.py
│   │   ├── yahoo_client.py
│   │   ├── byma_client.py
│   │   ├── multi_market_client.py
│   │   └── ... (todos los conectores)
│   │
│   ├── services/                   # Todos los servicios (36 archivos) ✅
│   │   ├── telegram_bot.py
│   │   ├── telegram_command_handler.py
│   │   ├── sentiment_analysis.py
│   │   ├── enhanced_sentiment.py
│   │   ├── news_fetcher.py
│   │   ├── risk_manager.py
│   │   ├── adaptive_risk_manager.py
│   │   ├── prediction_service.py
│   │   ├── technical_analysis.py
│   │   └── ... (todos los servicios)
│   │
│   ├── models/                     # Modelos de IA ✅
│   │   ├── price_predictor.py
│   │   └── technical_analyzer.py
│   │
│   ├── core/                       # Utilidades core (19 archivos) ✅
│   │   ├── logger.py
│   │   ├── safe_logger.py
│   │   ├── safe_print.py
│   │   ├── database.py
│   │   └── ... (todas las utilidades)
│   │
│   └── utils/                      # Utilidades generales ✅
│
├── 📂 scripts/ (Scripts de utilidad copiados) ✅
│   ├── train_model.py
│   ├── ingest_data.py
│   ├── verify_db.py
│   └── ... (todos los scripts)
│
├── 📂 features/ (Para nuevas funcionalidades)
│   └── _template_feature.py       # Template ✅
│
├── 📂 tests/ (Para tests de features nuevas)
│
└── 📂 docs/ (Documentación)
    ├── INTEGRATION_GUIDE.md        # Guía de integración ✅
    └── TEST_BOT_README.md          # Este archivo ✅
```

---

## ✅ Lo que se Copió

### Archivos Principales:
- ✅ `trading_bot.py` (159KB, 3167 líneas)
- ✅ `dashboard.py` (247KB, 4982 líneas)
- ✅ `run_bot.py` (launcher)
- ✅ `cli.py` (interfaz CLI)

### Carpeta src/ Completa:
- ✅ `connectors/` - Todos los conectores (IOL, Yahoo, BYMA, etc.)
- ✅ `services/` - Todos los servicios (36 archivos)
- ✅ `models/` - Modelos de IA
- ✅ `core/` - Utilidades core (19 archivos)
- ✅ `utils/` - Utilidades generales

### Configuraciones:
- ✅ `professional_config.json`
- ✅ `my_portfolio.json`
- ✅ `testing_config.json`
- ✅ `.env` (credenciales)

### Scripts:
- ✅ Todos los scripts de utilidad copiados

---

## 🎯 Cómo Usar test_bot/

### Opción 1: Ejecutar Test Bot Interactivo

```powershell
cd test_bot
..\venv\Scripts\python.exe test_trading_bot.py
```

Esto inicia un menú interactivo con opciones de testing.

### Opción 2: Ejecutar Bot de Test Completo

```powershell
cd test_bot
..\venv\Scripts\python.exe test_sistema_completo.py
```

Prueba el sistema completo con todos los servicios.

### Opción 3: Ejecutar Dashboard de Test

```powershell
cd test_bot
..\venv\Scripts\python.exe -m streamlit run dashboard.py --server.port 8502
```

**⚠️ IMPORTANTE**: Usa puerto **8502** (no 8501) para no conflictar con el dashboard de producción.

### Opción 4: Ejecutar Bot de Test en Modo Continuo

```powershell
cd test_bot
..\venv\Scripts\python.exe run_bot.py --paper --continuous --interval 5
```

Ejecuta el bot de test en modo continuo con intervalo de 5 minutos.

---

## 🛡️ Protección del Bot de Producción

### ✅ Garantías:

1. **Archivos separados**: Todo en `test_bot/` es independiente
2. **PID separados**: El test bot NO sobrescribe `bot.pid`
3. **Configs separadas**: Usa `test_bot/configs/`
4. **Paper Trading**: Test bot SIEMPRE en modo paper
5. **Puerto diferente**: Dashboard test en 8502 (producción en 8501)

### 🔒 El Bot de Producción:

- ✅ **Sigue funcionando** normalmente
- ✅ **NO se ve afectado** por cambios en `test_bot/`
- ✅ **Usa sus propios archivos** en la raíz del proyecto
- ✅ **Capital real protegido** ($21,891.65 ARS)

---

## 🔧 Modificaciones Permitidas en test_bot/

### ✅ Puedes Modificar Libremente:

**TODO dentro de `test_bot/` es seguro para modificar**:

- ✅ `test_bot/trading_bot.py` - Modifica el motor
- ✅ `test_bot/dashboard.py` - Modifica el dashboard
- ✅ `test_bot/src/services/*` - Modifica servicios
- ✅ `test_bot/src/connectors/*` - Modifica conectores
- ✅ `test_bot/configs/*` - Modifica configuraciones

### 🎯 Workflow de Modificación:

```
1. Modificar archivo en test_bot/
   ↓
2. Probar: python test_bot/archivo_modificado.py
   ↓
3. Si funciona → Anotar cambios
   ↓
4. Si está validado → Copiar cambios a producción
   ↓
5. Reiniciar bot de producción para aplicar
```

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Modificar Threshold de Compra

```powershell
# 1. Editar test_bot/configs/professional_config.json
# Cambiar "buy_threshold": 25 → 20

# 2. Probar
cd test_bot
..\venv\Scripts\python.exe test_trading_bot.py
# Elegir opción 1 (ciclo único)

# 3. Observar resultados
# ¿Genera más señales de compra con threshold 20?

# 4. Si funciona bien, aplicar a producción:
# Editar ../professional_config.json (producción)
# Reiniciar bot de producción
```

### Ejemplo 2: Modificar Mensaje de Telegram

```powershell
# 1. Editar test_bot/src/services/telegram_command_handler.py
# Modificar mensaje de /help

# 2. Probar
cd test_bot
..\venv\Scripts\python.exe run_bot.py --paper --continuous
# Enviar /help al bot

# 3. Si funciona, copiar cambios a producción:
# Copiar el método _handle_help() a:
# ../src/services/telegram_command_handler.py

# 4. Reiniciar bot de producción
```

### Ejemplo 3: Agregar Nueva Feature

```powershell
# 1. Crear nueva feature
# test_bot/features/mi_nueva_feature.py

# 2. Integrar en test_bot/trading_bot.py
# Agregar en __init__() o en _init_optional_features()

# 3. Probar
cd test_bot
..\venv\Scripts\python.exe test_trading_bot.py

# 4. Si funciona, copiar TODO:
# - test_bot/features/mi_nueva_feature.py → ../src/services/
# - Cambios en test_bot/trading_bot.py → ../trading_bot.py

# 5. Activar en producción
```

---

## 🚀 Scripts de Ejecución Rápida

Crea estos archivos `.bat` en `test_bot/` para ejecución rápida:

### `ejecutar_test_bot.bat`:
```bat
@echo off
cd %~dp0
..\venv\Scripts\python.exe test_trading_bot.py
pause
```

### `ejecutar_dashboard_test.bat`:
```bat
@echo off
cd %~dp0
..\venv\Scripts\python.exe -m streamlit run dashboard.py --server.port 8502
```

### `ejecutar_bot_continuo_test.bat`:
```bat
@echo off
cd %~dp0
..\venv\Scripts\python.exe run_bot.py --paper --continuous --interval 5
pause
```

---

## 📊 Diferencias entre Test y Producción

| Aspecto | Producción | Test Bot |
|---------|-----------|----------|
| **Ubicación** | `/financial_ai/` | `/financial_ai/test_bot/` |
| **Modo** | LIVE ($21,891 reales) | PAPER ($10,000 simulados) |
| **Dashboard Port** | 8501 | 8502 |
| **PID File** | `bot.pid` | `test_bot_pid.txt` |
| **Config** | `professional_config.json` | `test_bot/configs/` |
| **Modificable** | ❌ Con cuidado | ✅ Libremente |
| **Objetivo** | Trading real | Testing y desarrollo |

---

## 💡 Ventajas de Esta Estructura

1. ✅ **Desarrollo seguro**: Modifica sin miedo en `test_bot/`
2. ✅ **Testing completo**: Prueba TODO antes de producción
3. ✅ **Independencia**: Test bot no afecta producción
4. ✅ **Reversibilidad**: Fácil volver atrás si algo falla
5. ✅ **Experimentación**: Prueba configuraciones extremas sin riesgo
6. ✅ **Aprendizaje**: Entiende cómo funciona modificando la copia

---

## ⚠️ Notas Importantes

### 🔒 Archivos Sensibles:
- `.env` copiado en `test_bot/.env`
- Contiene credenciales reales (IOL, Telegram)
- **NO commitear** a Git
- Agregar `test_bot/.env` a `.gitignore`

### 💾 Base de Datos:
- Test bot usa las **mismas bases de datos** que producción
- Para datos independientes, copia también:
  - `trading_bot.db` → `test_bot/trading_bot_test.db`
  - Modifica conexión en `test_bot/src/core/database.py`

### 🔄 Sincronización:
- Cambios en `test_bot/` **NO se reflejan** automáticamente en producción
- Debes **copiar manualmente** los cambios validados
- Usa diff/compare para ver diferencias antes de copiar

---

## 🎯 Próximos Pasos

Ahora que tienes la copia completa:

1. **Probar el test bot** - Verificar que funciona
2. **Modificar algo** - Experimenta con cambios
3. **Validar** - Confirma que funciona
4. **Integrar** - Copia cambios a producción

---

**🤖 Ready para desarrollo seguro!** 🚀

