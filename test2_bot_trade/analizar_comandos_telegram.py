"""
Script para analizar comandos recibidos por Telegram y sus respuestas
"""

import re
from pathlib import Path
from datetime import datetime

def analizar_logs_telegram():
    """Analiza los logs para encontrar comandos de Telegram"""
    
    log_dir = Path("logs")
    if not log_dir.exists():
        print("❌ No se encontró el directorio de logs")
        return
    
    # Buscar el log más reciente
    log_files = sorted(log_dir.glob("trading_bot_*.log"), reverse=True)
    
    if not log_files:
        print("❌ No se encontraron archivos de log")
        return
    
    log_file = log_files[0]
    print(f"📄 Analizando: {log_file.name}\n")
    
    comandos_recibidos = []
    respuestas_enviadas = []
    
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        contenido = f.read()
    
    # Buscar mensajes recibidos
    patron_mensaje = r"📨 Mensaje recibido de (.+?): '(.+?)'"
    mensajes = re.findall(patron_mensaje, contenido)
    
    # Buscar comandos detectados
    patron_comando = r"🔍 Comando detectado: (.+?) \(args: (.+?)\)"
    comandos = re.findall(patron_comando, contenido)
    
    # Buscar ejecución de comandos
    patron_ejecucion = r"⚙️  Ejecutando comando: (.+?)"
    ejecuciones = re.findall(patron_ejecucion, contenido)
    
    # Buscar mensajes enviados
    patron_envio = r"📤 Enviando mensaje a chat_id (.+?)\.\.\."
    envios = re.findall(patron_envio, contenido)
    
    # Buscar confirmaciones de envío
    patron_confirmacion = r"✅ Mensaje enviado exitosamente"
    confirmaciones = re.findall(patron_confirmacion, contenido)
    
    # Buscar errores
    patron_error = r"❌ Error (.+?):"
    errores = re.findall(patron_error, contenido)
    
    print("=" * 60)
    print("📊 ANÁLISIS DE COMANDOS TELEGRAM")
    print("=" * 60)
    print()
    
    print(f"📨 Mensajes recibidos: {len(mensajes)}")
    if mensajes:
        print("\n   Últimos mensajes:")
        for usuario, mensaje in mensajes[-5:]:
            print(f"   • {usuario}: {mensaje}")
    
    print(f"\n🔍 Comandos detectados: {len(comandos)}")
    if comandos:
        print("\n   Comandos:")
        for comando, args in comandos[-10:]:
            args_display = args if args else "(sin argumentos)"
            print(f"   • {comando} {args_display}")
    
    print(f"\n⚙️  Comandos ejecutados: {len(ejecuciones)}")
    if ejecuciones:
        print("\n   Ejecuciones:")
        for cmd in ejecuciones[-10:]:
            print(f"   • {cmd}")
    
    print(f"\n📤 Mensajes enviados: {len(envios)}")
    print(f"✅ Confirmaciones de envío: {len(confirmaciones)}")
    
    if errores:
        print(f"\n❌ Errores encontrados: {len(errores)}")
        print("\n   Últimos errores:")
        for error in errores[-5:]:
            print(f"   • {error}")
    
    print("\n" + "=" * 60)
    print("💡 RESUMEN")
    print("=" * 60)
    print(f"   Total mensajes recibidos: {len(mensajes)}")
    print(f"   Total comandos procesados: {len(comandos)}")
    print(f"   Total mensajes enviados: {len(envios)}")
    print(f"   Tasa de éxito: {len(confirmaciones)/len(envios)*100:.1f}%" if envios else "   Tasa de éxito: N/A")
    
    # Buscar patrones específicos de comandos
    print("\n" + "=" * 60)
    print("📋 COMANDOS MÁS USADOS")
    print("=" * 60)
    
    comandos_count = {}
    for comando, _ in comandos:
        comandos_count[comando] = comandos_count.get(comando, 0) + 1
    
    if comandos_count:
        for cmd, count in sorted(comandos_count.items(), key=lambda x: x[1], reverse=True):
            print(f"   {cmd}: {count} veces")

if __name__ == "__main__":
    analizar_logs_telegram()

