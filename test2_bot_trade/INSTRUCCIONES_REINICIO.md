# 🔄 Instrucciones para Reiniciar el Bot con Universo Completo

## ✅ Verificación Pre-Reinicio

1. **Verificar que el bot está detenido:**
   ```powershell
   cd financial_ai/test2_bot_trade
   if (Test-Path "bot.pid") { Write-Host "Bot aún corriendo" } else { Write-Host "✅ Bot detenido" }
   ```

2. **Verificar configuración:**
   - El archivo `professional_config.json` debe tener:
     ```json
     "monitoring": {
       "use_full_universe": true,
       "max_symbols": 500,
       "universe_categories": ["acciones", "cedears", "bonos", "obligaciones", "letras"]
     }
     ```

## 🚀 Reiniciar desde el Dashboard

### Opción 1: Desde el Dashboard (Recomendado)

1. **Abrir el Dashboard:**
   - Ve a: http://localhost:8503
   - O ejecuta: `streamlit run dashboard.py --server.port 8503`

2. **Ir a "🤖 Bot Autónomo":**
   - En el menú lateral, selecciona "🤖 Bot Autónomo"
   - Abre el tab "🎮 Control del Bot"

3. **Configurar y Iniciar:**
   - **Modo:** Selecciona "💰 Live Trading (Dinero Real)"
   - **Intervalo:** 60 minutos (o el que prefieras)
   - **Opciones Avanzadas:**
     - ✅ Marca "🌐 Modo Universo Completo" (IMPORTANTE)
     - Opcional: "💬 Activar Chat Interactivo"
   - **Confirmación LIVE:** Marca el checkbox de confirmación
   - **Clic en:** "🚀 Iniciar Bot Autónomo (LIVE)"

4. **Verificar Inicio:**
   - El bot debería mostrar: "🌍 MODO UNIVERSO COMPLETO ACTIVADO"
   - Debería cargar múltiples símbolos (hasta 500 según configuración)
   - Verás mensajes como: "✅ UNIVERSO COMPLETO CARGADO: X instrumentos"

### Opción 2: Desde Terminal (Alternativa)

```powershell
cd financial_ai/test2_bot_trade
python trading_bot.py --live --continuous --interval 60
```

**Nota:** Esta opción usará la configuración de `professional_config.json` automáticamente.

## 📊 Verificar que Cargó Correctamente

Después de iniciar, deberías ver en los logs:

```
🌍 MODO UNIVERSO COMPLETO ACTIVADO
📊 Cargando TODOS los instrumentos disponibles en IOL...
✅ UNIVERSO COMPLETO CARGADO: XXX instrumentos
   Categorías incluidas:
   • ACCIONES: XX instrumentos
   • CEDEARS: XX instrumentos
   • BONOS: XX instrumentos
   ...
```

## ⚠️ Si No Carga el Universo Completo

1. **Verificar configuración:**
   ```powershell
   python -c "import json; config = json.load(open('professional_config.json')); print('use_full_universe:', config['monitoring']['use_full_universe'])"
   ```

2. **Forzar configuración desde Dashboard:**
   - Ve a "⚙️ Sistema & Configuración"
   - Tab "🌍 Configuración de Análisis"
   - Selecciona "🌍 Universo Completo de IOL"
   - Configura categorías y max_symbols
   - Guarda configuración
   - Reinicia el bot

## 🔍 Monitorear el Bot

Una vez iniciado, puedes:

1. **Ver estado en Dashboard:**
   - "🤖 Bot Autónomo" → "🎮 Control del Bot"
   - Verás estadísticas, operaciones recientes, etc.

2. **Verificar con script:**
   ```powershell
   python verificar_bot_live.py
   ```

3. **Comandos Telegram:**
   - `/status` - Estado del bot
   - `/symbols` - Símbolos monitoreados
   - `/restart` - Reiniciar ciclo de análisis

## 📝 Notas Importantes

- **Primera carga puede tardar:** La carga inicial del universo completo puede tomar 2-5 minutos
- **Datos históricos:** El bot descargará automáticamente datos históricos si tiene menos de 30 registros por símbolo
- **Límite de símbolos:** Si hay más de `max_symbols`, se priorizan CEDEARs y acciones principales

