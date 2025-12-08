"""
Cursor Task Listener - Sistema de Cola de Tareas
Escucha comandos de Telegram y los guarda para que Cursor los procese

Flujo:
1. Usuario envía /dev_task [solicitud] por Telegram
2. Este script guarda la solicitud en cursor_tasks.json
3. Cursor lee cursor_tasks.json y ejecuta la tarea
4. Cursor marca como completada y responde por Telegram
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Archivos de tareas
TASKS_FILE = Path("cursor_tasks.json")
RESPONSES_FILE = Path("cursor_responses.json")

class CursorTaskListener:
    """Escucha Telegram y guarda tareas para Cursor"""
    
    def __init__(self):
        self.token = TOKEN
        self.chat_id = CHAT_ID
        self.last_update_id = 0
        self.running = False
        
        # Inicializar archivo de tareas si no existe
        if not TASKS_FILE.exists():
            TASKS_FILE.write_text(json.dumps({"tasks": []}, indent=2))
        
        if not RESPONSES_FILE.exists():
            RESPONSES_FILE.write_text(json.dumps({"responses": []}, indent=2))
        
        print("✅ Cursor Task Listener inicializado")
    
    def _send_message(self, text):
        """Envía mensaje a Telegram"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {"chat_id": self.chat_id, "text": text, "parse_mode": None}
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error enviando: {e}")
            return False
    
    def _get_updates(self):
        """Obtiene mensajes de Telegram"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            params = {"offset": self.last_update_id + 1, "timeout": 10}
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    updates = data.get('result', [])
                    if updates:
                        self.last_update_id = max(u.get('update_id', 0) for u in updates)
                    return updates
            return []
        except Exception as e:
            print(f"⚠️  Error: {e}")
            return []
    
    def _add_task(self, task_text):
        """Agrega una tarea a la cola"""
        try:
            # Leer tareas actuales
            with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Agregar nueva tarea
            task = {
                "id": int(time.time()),
                "timestamp": datetime.now().isoformat(),
                "request": task_text,
                "status": "pending",
                "created_by": "telegram"
            }
            
            data["tasks"].append(task)
            
            # Guardar
            with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Tarea agregada: {task_text[:50]}...")
            return task["id"]
            
        except Exception as e:
            print(f"❌ Error agregando tarea: {e}")
            return None
    
    def _check_responses(self):
        """Verifica si Cursor ha respondido tareas"""
        try:
            if not RESPONSES_FILE.exists():
                return
            
            with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            responses = data.get("responses", [])
            new_responses = [r for r in responses if r.get("sent_to_telegram") != True]
            
            for response in new_responses:
                # Enviar respuesta por Telegram
                mensaje = f"""✅ TAREA COMPLETADA

ID: {response.get('task_id')}
Solicitud: {response.get('request', '')[:100]}

Respuesta de Cursor:
{response.get('response', '')[:700]}

Hora: {response.get('timestamp', '')}"""
                
                if self._send_message(mensaje):
                    # Marcar como enviada
                    response["sent_to_telegram"] = True
            
            # Guardar
            if new_responses:
                with open(RESPONSES_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️  Error revisando respuestas: {e}")
    
    def _process_message(self, update):
        """Procesa mensaje de Telegram"""
        try:
            message = update.get('message', {})
            if not message:
                return
            
            text = message.get('text', '').strip()
            chat_id = str(message.get('chat', {}).get('id', ''))
            
            # Verificar autorización
            if chat_id != str(self.chat_id):
                return
            
            # Comando /dev_task
            if text.startswith('/dev_task '):
                task_text = text.replace('/dev_task ', '', 1).strip()
                
                if not task_text:
                    self._send_message("❌ Uso: /dev_task [solicitud]\n\nEjemplo:\n/dev_task agregar feature de trailing stop loss")
                    return
                
                print(f"📨 Nueva solicitud: {task_text}")
                
                task_id = self._add_task(task_text)
                
                if task_id:
                    self._send_message(f"""✅ SOLICITUD RECIBIDA

ID: {task_id}
Solicitud: {task_text}

⏳ Cursor procesara tu solicitud
📱 Te notificare cuando este completada

Estado: PENDIENTE""")
                else:
                    self._send_message("❌ Error guardando solicitud")
            
            # Comando /dev_tasks (listar tareas)
            elif text == '/dev_tasks':
                with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                tasks = data.get("tasks", [])
                pending = [t for t in tasks if t.get("status") == "pending"]
                completed = [t for t in tasks if t.get("status") == "completed"]
                
                mensaje = f"""📋 ESTADO DE TAREAS

⏳ Pendientes: {len(pending)}
✅ Completadas: {len(completed)}

Ultimas pendientes:"""
                
                for task in pending[-5:]:
                    mensaje += f"\n• ID {task.get('id')}: {task.get('request', '')[:50]}"
                
                self._send_message(mensaje)
            
            # Comando /dev_clear (limpiar tareas completadas)
            elif text == '/dev_clear':
                with open(TASKS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                pending = [t for t in data.get("tasks", []) if t.get("status") == "pending"]
                data["tasks"] = pending
                
                with open(TASKS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self._send_message("✅ Tareas completadas eliminadas")
                
        except Exception as e:
            print(f"❌ Error procesando: {e}")
    
    def start(self):
        """Inicia el listener"""
        print()
        print("="*70)
        print("🎯 CURSOR TASK LISTENER - Sistema de Cola de Tareas")
        print("="*70)
        print()
        print("📱 Escuchando Telegram para solicitudes a Cursor...")
        print()
        print("Comandos disponibles:")
        print("  /dev_task [solicitud] - Enviar tarea a Cursor")
        print("  /dev_tasks - Ver tareas pendientes")
        print("  /dev_clear - Limpiar completadas")
        print()
        print("📝 Ejemplos:")
        print("  /dev_task agregar feature de trailing stop loss")
        print("  /dev_task mejorar el dashboard con graficos")
        print("  /dev_task fix el error de datos insuficientes")
        print()
        print("⏳ Presiona Ctrl+C para detener")
        print("="*70)
        print()
        
        # Mensaje de inicio
        self._send_message(f"""🎯 CURSOR TASK LISTENER INICIADO

⏰ {datetime.now().strftime('%H:%M:%S')}

Ahora puedes enviar solicitudes a Cursor:

📝 Comandos:
/dev_task [solicitud] - Nueva tarea
/dev_tasks - Ver pendientes
/dev_clear - Limpiar completadas

📋 Ejemplos:
/dev_task agregar trailing stop
/dev_task mejorar dashboard
/dev_task fix error X

✅ Listener activo""")
        
        self.running = True
        
        try:
            check_count = 0
            while self.running:
                # Obtener mensajes
                updates = self._get_updates()
                
                for update in updates:
                    self._process_message(update)
                
                # Revisar si hay respuestas de Cursor
                self._check_responses()
                
                # Log cada 30 checks
                check_count += 1
                if check_count % 30 == 1:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Escuchando... (check #{check_count})")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n🛑 Listener detenido")
            self._send_message("🛑 Cursor Task Listener detenido")
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            self.running = False
            print("✅ Listener finalizado")

if __name__ == "__main__":
    try:
        listener = CursorTaskListener()
        listener.start()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()

