# 🛠️ Cursor Telegram Controller

## ¿Qué es?

Sistema que permite **controlar Cursor y el desarrollo desde Telegram**.

Con esto puedes:
- ✅ Ver estado del sistema
- ✅ Reiniciar bots (test/producción)
- ✅ Crear backups
- ✅ Ver logs en tiempo real
- ✅ Ejecutar comandos de sistema
- ✅ Comparar configuraciones
- ✅ Aplicar cambios de test a producción
- ✅ **Todo desde tu teléfono** 📱

---

## 🚀 Cómo Usar

### 1. Iniciar el Controller:

```powershell
cd financial_ai
.\ejecutar_cursor_controller.bat
```

O directamente:

```powershell
.\venv\Scripts\python.exe test_bot\features\cursor_telegram_controller.py
```

### 2. Desde Telegram:

Abre tu bot (`@Preoyect_bot`) y envía comandos con prefijo `/dev_`

---

## 📋 Comandos Disponibles

### 🔍 Monitoreo

#### `/dev_status`
Muestra estado completo del sistema

**Respuesta:**
```
📊 ESTADO DEL SISTEMA DE DESARROLLO

⏰ Hora: 13:00:00

🤖 Bot de Test:
✅ CORRIENDO
Ubicacion: /test_bot/
Archivos: 45 archivos Python

🚀 Bot de Produccion:
✅ FUNCIONANDO
Ubicacion: /financial_ai/

✅ Sistema listo para desarrollo
```

#### `/dev_logs`
Ver últimas 20 líneas de logs

---

### 🔄 Control

#### `/dev_restart_test`
Reinicia el bot de test

**Acción:**
1. Detiene bot actual
2. Inicia nuevo bot de test
3. Confirma reinicio

**Respuesta:**
```
✅ BOT DE TEST REINICIADO

⏰ Hora: 13:00:00
🎯 Estado: INICIANDO
📊 Modo: PAPER TRADING

El bot esta analizando...
```

#### `/dev_restart_prod`
Reinicia bot de producción (CON CONFIRMACIÓN)

**⚠️ CUIDADO:** Requiere confirmación adicional por seguridad

---

### 💾 Desarrollo

#### `/dev_backup`
Crea un backup automático

**Acción:**
- Ejecuta `backup_estado_estable.py`
- Guarda estado actual completo
- Te permite rollback si algo sale mal

**Respuesta:**
```
✅ BACKUP CREADO

⏰ Hora: 13:00:00
📁 Ubicacion: backups/
✅ Sistema respaldado
```

#### `/dev_compare`
Compara configuraciones test vs producción

**Respuesta:**
```
📊 COMPARACION DE CONFIGURACIONES

Test Bot vs Produccion

DIFERENCIAS:
• buy_threshold:
  Test: 0
  Prod: 20
• min_confidence:
  Test: LOW
  Prod: MEDIUM
```

#### `/dev_test_feature`
Lista features disponibles para testear

#### `/dev_apply_changes`
Aplica cambios de test_bot a producción

**⚠️ IMPORTANTE:** 
- Requiere confirmación
- Crea backup automático primero
- Solo para cambios testeados

---

### ⚡ Ejecución

#### `/dev_exec [comando]`
Ejecuta un comando de sistema

**Ejemplos:**

```
/dev_exec python diagnosticar_bot.py
/dev_exec python scripts/verify_db.py
/dev_exec dir test_bot
```

**Respuesta:**
```
✅ COMANDO EJECUTADO

Comando: python diagnosticar_bot.py
Codigo de salida: 0

Salida:
[output del comando]
```

**⚠️ Seguridad:**
- Solo tu chat_id puede ejecutar
- Timeout de 30 segundos
- Output limitado a 1000 caracteres

---

### ℹ️ Ayuda

#### `/dev_help`
Muestra todos los comandos disponibles

---

## 🎯 Casos de Uso

### Caso 1: Monitoreo Remoto

Estás fuera de casa y quieres ver el estado:

```
Tú: /dev_status
Bot: [Estado completo del sistema]

Tú: /dev_logs
Bot: [Últimos logs]
```

### Caso 2: Reinicio de Emergencia

El bot tiene problemas:

```
Tú: /dev_restart_test
Bot: 🔄 Reiniciando bot de test...
Bot: ✅ BOT DE TEST REINICIADO
```

### Caso 3: Desarrollo y Testing

Probaste una feature y funciona bien:

```
Tú: /dev_backup
Bot: ✅ BACKUP CREADO

Tú: /dev_compare
Bot: [Diferencias entre test y prod]

Tú: /dev_apply_changes
Bot: [Instrucciones de confirmación]
```

### Caso 4: Debugging

Necesitas ejecutar un diagnóstico:

```
Tú: /dev_exec python diagnosticar_ordenes.py
Bot: ✅ COMANDO EJECUTADO
     [Output del diagnóstico]
```

---

## 🔐 Seguridad

### ✅ Características de Seguridad:

1. **Autenticación por Chat ID**
   - Solo tu Telegram puede controlar
   - Otros chats son rechazados

2. **Confirmaciones para Acciones Críticas**
   - Reinicio de producción: Doble confirmación
   - Aplicar cambios: Confirmación con nombre de archivo
   - Comandos destructivos bloqueados

3. **Timeouts**
   - Comandos limitados a 30 segundos
   - Evita procesos colgados

4. **Prefijo `/dev_`**
   - Separa comandos de desarrollo de trading
   - Evita confusiones

5. **Output Limitado**
   - Máximo 1000 caracteres por mensaje
   - Evita spam en Telegram

---

## 🔧 Arquitectura

```
┌──────────────────┐
│   Telegram       │
│   (Tu teléfono)  │
└────────┬─────────┘
         │ /dev_status
         ▼
┌──────────────────────────────┐
│  Cursor Telegram Controller  │
│  (Python Script)             │
│                              │
│  • Recibe comandos           │
│  • Valida autorización       │
│  • Ejecuta acciones          │
│  • Envía respuestas          │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  Sistema de Archivos         │
│                              │
│  • test_bot/                 │
│  • financial_ai/             │
│  • logs/                     │
│  • backups/                  │
└──────────────────────────────┘
```

---

## 🚨 Limitaciones y Advertencias

### ⚠️ Comandos que NO deberías ejecutar:

- ❌ `rm -rf` o equivalentes destructivos
- ❌ Comandos que modifiquen credenciales
- ❌ Scripts que no conoces

### ⚠️ Buenas Prácticas:

- ✅ Siempre crear backup antes de cambios grandes
- ✅ Probar en test_bot antes de aplicar a producción
- ✅ Revisar logs después de reiniciar
- ✅ Confirmar estado con `/dev_status`

---

## 📝 Registro de Comandos

El controller registra todos los comandos ejecutados:

```
📨 Comando de desarrollo: /dev_status
⚙️  Ejecutando: /dev_status
✅ Respuesta enviada
```

---

## 🔄 Workflow Recomendado

### Desarrollo Normal:

```
1. /dev_status → Verificar sistema
2. Modificar en Cursor
3. /dev_restart_test → Probar cambios
4. /dev_logs → Verificar que funciona
5. /dev_backup → Guardar estado estable
6. /dev_apply_changes → Aplicar a producción
```

### Debugging:

```
1. /dev_logs → Ver qué pasó
2. /dev_status → Estado actual
3. /dev_exec python diagnosticar_bot.py
4. /dev_restart_test → Reintentar
```

### Monitoreo:

```
1. /dev_status → Check rápido
2. /dev_logs → Ver actividad reciente
3. (Repetir cada X horas)
```

---

## 🎉 Ventajas

### ✅ Desarrollo Remoto:
- Controla desde cualquier lugar
- No necesitas estar en la PC
- Responde a alertas rápidamente

### ✅ Productividad:
- Comandos rápidos desde el teléfono
- Sin abrir terminal
- Multitarea mientras monitoreas

### ✅ Seguridad:
- Backups antes de cambios
- Confirmaciones para acciones críticas
- Rollback fácil

### ✅ Monitoreo:
- Estado en tiempo real
- Logs instantáneos
- Alertas integradas

---

## 🐛 Troubleshooting

### Controller no inicia:

```powershell
# Verificar .env
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Token:', os.getenv('TELEGRAM_BOT_TOKEN')[:15])"

# Verificar dependencias
pip install requests python-dotenv
```

### Comandos no responden:

1. Verifica que el controller esté corriendo
2. Envía `/dev_help` para test
3. Revisa que tu chat_id sea correcto

### Error de permisos:

- Ejecuta como administrador si es necesario
- Verifica permisos de archivos

---

## 📦 Instalación

Ya está todo instalado en tu proyecto.

**Para iniciar:**

```powershell
cd financial_ai
.\ejecutar_cursor_controller.bat
```

**Verás:**

```
🚀 CURSOR TELEGRAM CONTROLLER INICIADO
📱 Escuchando comandos de desarrollo en Telegram...
💡 Envia /dev_help para ver comandos disponibles
```

**En Telegram recibirás:**

```
🛠️ CURSOR CONTROLLER INICIADO
✅ Controller activo y escuchando...
```

---

## 🎓 Conclusión

Con **Cursor Telegram Controller** puedes:

- 🔧 **Desarrollar** desde tu teléfono
- 📊 **Monitorear** el sistema remotamente
- 🚀 **Controlar** bots sin estar en la PC
- 💾 **Gestionar** backups y cambios
- ⚡ **Ejecutar** comandos a distancia

**¡Todo el poder de Cursor en tu Telegram!** 🎉

---

Desarrollado por: Antigravity + Claude
Fecha: 2025-12-02
Estado: ✅ Funcional y probado

