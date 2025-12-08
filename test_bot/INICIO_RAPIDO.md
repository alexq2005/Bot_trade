# 🚀 Inicio Rápido - Test Bot

Guía rápida para empezar a usar el Test Bot inmediatamente.

---

## ✅ ¿Qué es test_bot/?

Una **copia completa e independiente** del sistema IOL Quantum AI que puedes:
- ✅ Modificar libremente sin romper producción
- ✅ Probar nuevas funcionalidades
- ✅ Experimentar con configuraciones
- ✅ Desarrollar features nuevas

---

## 🎯 Inicio en 3 Pasos

### 1. Navega a test_bot/
```powershell
cd C:\Users\Lexus\.gemini\antigravity\scratch\financial_ai\test_bot
```

### 2. Ejecuta el Test Bot
```powershell
.\ejecutar_test_bot.bat
```

### 3. Elige una opción del menú
```
1. Ejecutar ciclo de análisis
2. Modo continuo
3. Analizar símbolo
... etc
```

**¡Listo!** 🎉

---

## 🌐 Dashboard de Test

Para ejecutar el dashboard de testing:

```powershell
cd test_bot
.\ejecutar_dashboard_test.bat
```

Luego abre: `http://localhost:8502`

---

## 📝 Archivos Principales en test_bot/

| Archivo | Descripción | Modificable |
|---------|-------------|-------------|
| `trading_bot.py` | Motor principal del bot | ✅ Sí |
| `dashboard.py` | Dashboard web | ✅ Sí |
| `run_bot.py` | Script de inicio | ✅ Sí |
| `src/` | Código fuente completo | ✅ Sí |
| `configs/professional_config.json` | Configuración | ✅ Sí |
| `.env` | Credenciales | ⚠️ Cuidado |

**TODO es modificable sin afectar producción** ✅

---

## 🔧 Modificaciones Comunes

### Cambiar Parámetros de Riesgo:

1. Edita: `test_bot/configs/professional_config.json`
2. Cambia valores (ej: `"buy_threshold": 20`)
3. Ejecuta: `.\ejecutar_test_bot.bat`
4. Observa diferencias

### Modificar Código del Bot:

1. Edita: `test_bot/trading_bot.py`
2. Guarda cambios
3. Ejecuta: `.\ejecutar_test_bot.bat`
4. Prueba funcionalidad

### Modificar Dashboard:

1. Edita: `test_bot/dashboard.py`
2. Ejecuta: `.\ejecutar_dashboard_test.bat`
3. Abre `http://localhost:8502`
4. Valida cambios visualmente

---

## 🛡️ Protección Garantizada

### ✅ El Bot de Producción:
- Sigue corriendo normalmente
- Usa archivos en `/financial_ai/` (raíz)
- Capital real protegido ($21,891.65)
- PID: Diferente del test bot

### ✅ El Test Bot:
- Completamente independiente
- Usa archivos en `/financial_ai/test_bot/`
- Modo PAPER TRADING obligatorio
- Capital simulado ($10,000)

---

## 🎯 Casos de Uso

### Caso 1: Probar Nuevo Threshold

```powershell
# En test_bot/configs/professional_config.json
"buy_threshold": 15  # Más agresivo

# Ejecutar
cd test_bot
.\ejecutar_test_bot.bat
# Opción 1: Ciclo único

# Observar: ¿Más señales de compra?
```

### Caso 2: Modificar Mensaje de Telegram

```powershell
# Editar test_bot/src/services/telegram_command_handler.py
# Cambiar mensaje de /help

# Probar
cd test_bot
.\ejecutar_bot_continuo_test.bat

# Enviar /help al bot y ver nuevo mensaje
```

### Caso 3: Agregar Nueva Feature

```powershell
# Crear test_bot/features/mi_feature.py

# Integrar en test_bot/trading_bot.py

# Probar
cd test_bot
.\ejecutar_test_bot.bat
```

---

## 📋 Checklist de Uso

Antes de usar test_bot/:

```
□ Bot de producción está corriendo
□ Backup creado (ya hecho ✅)
□ test_bot/ tiene copia completa
□ Entiendes que cambios aquí NO afectan producción
```

Después de modificar test_bot/:

```
□ Cambios probados en test_bot/
□ Funcionalidad validada
□ Decidir si copiar a producción
□ Si copias: crear backup primero
```

---

## 🆘 Ayuda Rápida

### ¿El test bot no inicia?
```powershell
# Verificar que estás en test_bot/
cd C:\Users\Lexus\.gemini\antigravity\scratch\financial_ai\test_bot

# Verificar venv
..\venv\Scripts\python.exe --version
```

### ¿Quieres volver a empezar?
```powershell
# Eliminar test_bot/
cd ..
Remove-Item test_bot -Recurse -Force

# Restaurar desde backup
python restaurar_backup.py stable_20251202_114451_pre_test_bot_estructura

# (Luego volver a copiar estructura)
```

---

## 🚀 ¡Empieza Ahora!

```powershell
cd test_bot
.\ejecutar_test_bot.bat
```

**¡Y empieza a experimentar sin miedo!** 🎉

---

**Bot de Producción**: ✅ Protegido y funcionando  
**Test Bot**: ✅ Listo para modificar  
**Backup**: ✅ Disponible para rollback  

