"""
Cursor Task Processor - Procesa tareas y genera respuestas
Este script lo ejecuta Cursor para procesar tareas pendientes

Uso:
    python cursor_task_processor.py
    
    O simplemente leer cursor_tasks.json y ejecutar manualmente
"""

import json
from pathlib import Path
from datetime import datetime

TASKS_FILE = Path("cursor_tasks.json")
RESPONSES_FILE = Path("cursor_responses.json")

def load_tasks():
    """Carga tareas pendientes"""
    if not TASKS_FILE.exists():
        return []
    
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return [t for t in data.get("tasks", []) if t.get("status") == "pending"]

def mark_completed(task_id):
    """Marca una tarea como completada"""
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
    
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_response(task_id, request, response_text):
    """Agrega una respuesta"""
    if not RESPONSES_FILE.exists():
        data = {"responses": []}
    else:
        with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    response = {
        "task_id": task_id,
        "request": request,
        "response": response_text,
        "timestamp": datetime.now().isoformat(),
        "sent_to_telegram": False
    }
    
    data["responses"].append(response)
    
    with open(RESPONSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def show_pending_tasks():
    """Muestra tareas pendientes"""
    tasks = load_tasks()
    
    print()
    print("="*70)
    print("📋 TAREAS PENDIENTES PARA CURSOR")
    print("="*70)
    print()
    
    if not tasks:
        print("✅ No hay tareas pendientes")
        print()
        print("💡 El usuario puede enviar tareas desde Telegram con:")
        print("   /dev_task [solicitud]")
        print()
        return
    
    print(f"Total: {len(tasks)} tareas")
    print()
    
    for i, task in enumerate(tasks, 1):
        print(f"{i}. ID: {task.get('id')}")
        print(f"   📝 Solicitud: {task.get('request')}")
        print(f"   ⏰ Creada: {task.get('timestamp')}")
        print()
    
    print("="*70)
    print()
    print("💡 Para procesar estas tareas:")
    print("   1. Lee la solicitud")
    print("   2. Ejecuta la acción en Cursor")
    print("   3. Responde con:")
    print(f"      task_id = {tasks[0].get('id')}")
    print(f"      add_response(task_id, '{tasks[0].get('request', '')[:30]}...', 'Tu respuesta')")
    print(f"      mark_completed(task_id)")
    print()

if __name__ == "__main__":
    show_pending_tasks()

