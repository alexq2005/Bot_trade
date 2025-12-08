# 🚀 Comandos Rápidos - Test Bot

Guía rápida para ejecutar el Test Bot de diferentes formas.

---

## 🎮 Ejecución Interactiva

### Opción 1: Test Bot con Menú
```powershell
cd test_bot
.\ejecutar_test_bot.bat
```

**O manualmente:**
```powershell
cd test_bot
..\venv\Scripts\python.exe test_trading_bot.py
```

**Menú disponible:**
1. Ejecutar ciclo único
2. Modo continuo (5 min)
3. Analizar símbolo específico
4. Ver configuración
5. Probar features nuevas
6. Salir

---

## 🌐 Dashboard de Test

```powershell
cd test_bot
.\ejecutar_dashboard_test.bat
```

**O manualmente:**
```powershell
cd test_bot
..\venv\Scripts\python.exe -m streamlit run dashboard.py --server.port 8502
```

**Acceso:**
- URL: `http://localhost:8502`
- Puerto diferente al de producción (8501)

---

## 🔄 Bot Continuo de Test

```powershell
cd test_bot
.\ejecutar_bot_continuo_test.bat
```

**O manualmente:**
```powershell
cd test_bot
..\venv\Scripts\python.exe run_bot.py --paper --continuous --interval 5
```

**Características:**
- Modo: PAPER TRADING (simulado)
- Intervalo: 5 minutos (rápido para testing)
- Capital: Según config

---

## 🧪 Testing de Componentes Específicos

### Probar Predicción con IA
```powershell
cd test_bot
..\venv\Scripts\python.exe test_sistema_completo.py
# Elegir opción 5
```

### Probar Análisis Técnico
```powershell
cd test_bot
..\venv\Scripts\python.exe test_sistema_completo.py
# Elegir opción 6
```

### Probar Gestión de Riesgo
```powershell
cd test_bot
..\venv\Scripts\python.exe test_sistema_completo.py
# Elegir opción 7
```

### Ver Portafolio (Solo Lectura)
```powershell
cd test_bot
..\venv\Scripts\python.exe test_sistema_completo.py
# Elegir opción 3
```

---

## 🔧 Modificar y Probar Cambios

### Ejemplo: Cambiar Threshold de Compra

```powershell
# 1. Editar configuración
notepad test_bot\configs\professional_config.json
# Cambiar "buy_threshold": 25 → 20

# 2. Ejecutar test
cd test_bot
.\ejecutar_test_bot.bat
# Opción 1: Ejecutar ciclo único

# 3. Observar si genera más señales de compra

# 4. Si funciona bien, aplicar a producción:
notepad ..\professional_config.json  # Aplicar cambio
# Reiniciar bot de producción
```

### Ejemplo: Modificar Código del Bot

```powershell
# 1. Editar código
code test_bot\trading_bot.py
# Hacer modificaciones

# 2. Probar
cd test_bot
.\ejecutar_test_bot.bat

# 3. Si funciona, copiar cambios a producción:
# Usar diff para comparar:
# code --diff trading_bot.py ..\trading_bot.py
# Copiar solo los cambios validados
```

### Ejemplo: Modificar Dashboard

```powershell
# 1. Editar dashboard
code test_bot\dashboard.py
# Hacer modificaciones

# 2. Probar
cd test_bot
.\ejecutar_dashboard_test.bat
# Abrir http://localhost:8502

# 3. Validar cambios visualmente

# 4. Si funciona, copiar a producción
```

---

## 📊 Comparar con Producción

### Ver Diferencias:

```powershell
# Comparar trading_bot.py
code --diff test_bot\trading_bot.py trading_bot.py

# Comparar dashboard.py
code --diff test_bot\dashboard.py dashboard.py

# Comparar configs
code --diff test_bot\configs\professional_config.json professional_config.json
```

---

## 🔄 Actualizar test_bot/ desde Producción

Si la producción tiene cambios que quieres en test_bot/:

```powershell
# Copiar archivo específico
Copy-Item trading_bot.py -Destination test_bot\trading_bot.py -Force

# O rehacer copia completa
# (Guarda tus cambios en test_bot/ primero!)
```

---

## ⚠️ Precauciones

### Antes de Ejecutar en test_bot/:

1. ✅ Verificar que bot de producción está corriendo
2. ✅ Usar puerto diferente para dashboard (8502)
3. ✅ Confirmar modo PAPER TRADING
4. ✅ No modificar archivos de producción por accidente

### Al Copiar Cambios a Producción:

1. ✅ Crear backup antes
2. ✅ Probar en test_bot/ primero
3. ✅ Comparar archivos (diff)
4. ✅ Copiar solo cambios validados
5. ✅ Reiniciar bot de producción
6. ✅ Monitorear logs por 30 minutos

---

## 🎯 Flujo de Trabajo Recomendado

```
1. Modificar en test_bot/
   ↓
2. Probar con ejecutar_test_bot.bat
   ↓
3. Validar que funciona correctamente
   ↓
4. Crear backup de producción
   ↓
5. Copiar cambios a producción
   ↓
6. Reiniciar bot de producción
   ↓
7. Monitorear y confirmar que funciona
```

---

**🤖 Desarrollado por Antigravity + Claude** 🚀

