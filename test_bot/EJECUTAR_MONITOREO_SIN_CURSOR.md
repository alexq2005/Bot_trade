# 🚀 Ejecutar Monitoreo Continuo SIN CURSOR

## 📋 Instrucciones

### Método 1: Desde el Explorador de Windows

1. **Navega a la carpeta:**
   ```
   C:\Users\Lexus\.gemini\antigravity\scratch\financial_ai\test_bot
   ```

2. **Haz doble clic en:**
   ```
   iniciar_monitoreo_14dias.bat
   ```

3. **Se abrirá una ventana de comandos** con el monitoreo ejecutándose

4. **Puedes cerrar Cursor** - El monitoreo continuará funcionando

---

### Método 2: Desde la Línea de Comandos

1. **Abre PowerShell o CMD**

2. **Navega a la carpeta:**
   ```powershell
   cd C:\Users\Lexus\.gemini\antigravity\scratch\financial_ai\test_bot
   ```

3. **Ejecuta el script:**
   ```powershell
   .\iniciar_monitoreo_14dias.bat
   ```

---

## ✅ Características

- ✅ **Independiente de Cursor** - Funciona sin Cursor
- ✅ **Ventana separada** - Se ejecuta en su propia ventana
- ✅ **Verificación de Python** - Verifica que Python esté disponible
- ✅ **14 días de monitoreo** - Ejecución continua automática
- ✅ **Reportes diarios** - Envía notificaciones por Telegram

---

## 📊 Verificar el Progreso

### Opción 1: Ver la ventana del monitor
- Revisa la ventana que se abrió al ejecutar el script
- Muestra el progreso en tiempo real

### Opción 2: Ver archivo de monitoreo
```powershell
cd C:\Users\Lexus\.gemini\antigravity\scratch\financial_ai\test_bot
python ver_progreso_14dias.py
```

### Opción 3: Revisar archivo JSON
```
test_bot/data/monitoring_14dias.json
```

---

## 🛑 Detener el Monitoreo

1. **Cierra la ventana del monitor** (la que se abrió al ejecutar el script)
2. O presiona `Ctrl+C` en la ventana del monitor

---

## 📝 Notas Importantes

- El monitoreo se ejecuta durante **14 días** automáticamente
- Los datos se guardan en `data/monitoring_14dias.json`
- Los reportes diarios se envían por Telegram
- Puedes cerrar Cursor sin afectar el monitoreo
- El script verifica que Python esté disponible antes de ejecutar

---

## 🔧 Solución de Problemas

### Error: "Python no encontrado"
- Asegúrate de que Python esté instalado
- O activa el entorno virtual antes de ejecutar

### El monitoreo no inicia
- Verifica que `monitor_14_dias.py` exista en la carpeta
- Verifica que tengas permisos de ejecución

### No se reciben notificaciones de Telegram
- Verifica que `TELEGRAM_BOT_TOKEN` esté configurado en `.env`
- El monitoreo funcionará igual, solo sin notificaciones

---

**✅ El monitoreo está listo para ejecutarse de forma completamente independiente**

