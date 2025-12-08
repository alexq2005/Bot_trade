"""
Script de Backup Automático del Estado Estable
Crea una copia completa del sistema antes de hacer cambios
"""
import shutil
import os
import json
from datetime import datetime
from pathlib import Path

def crear_backup(descripcion=""):
    """
    Crea un backup completo del estado actual
    
    Args:
        descripcion: Descripción opcional del backup
    """
    print("="*70)
    print("💾 CREANDO BACKUP DEL ESTADO ESTABLE")
    print("="*70)
    print()
    
    # Timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"stable_{timestamp}"
    if descripcion:
        # Limpiar descripción para nombre de archivo
        desc_clean = descripcion.replace(' ', '_').replace('/', '_')
        backup_name += f"_{desc_clean}"
    
    backup_dir = Path(f"backups/{backup_name}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Directorio de backup: {backup_dir}")
    print()
    
    # Lista de archivos críticos a respaldar
    archivos_criticos = [
        'trading_bot.py',
        'dashboard.py',
        'run_bot.py',
        'cli.py',
        'professional_config.json',
        'my_portfolio.json',
        'trades.json',
        'risk_manager_history.json',
        '.env',
        'requirements.txt',
        'README.md'
    ]
    
    print("📄 Respaldando archivos críticos...")
    archivos_copiados = 0
    for archivo in archivos_criticos:
        if Path(archivo).exists():
            try:
                shutil.copy(archivo, backup_dir / archivo)
                print(f"  ✅ {archivo}")
                archivos_copiados += 1
            except Exception as e:
                print(f"  ⚠️  {archivo}: {e}")
        else:
            print(f"  ⏭️  {archivo} (no existe)")
    
    print()
    print("📂 Respaldando carpetas completas...")
    
    # Carpetas a respaldar
    carpetas = ['src', 'scripts', 'tests', 'config', 'models']
    carpetas_copiadas = 0
    
    for carpeta in carpetas:
        if Path(carpeta).exists():
            try:
                dest = backup_dir / carpeta
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(carpeta, dest)
                
                # Contar archivos
                archivos_en_carpeta = len(list(dest.rglob('*')))
                print(f"  ✅ {carpeta}/ ({archivos_en_carpeta} archivos)")
                carpetas_copiadas += 1
            except Exception as e:
                print(f"  ⚠️  {carpeta}/: {e}")
        else:
            print(f"  ⏭️  {carpeta}/ (no existe)")
    
    print()
    
    # Crear archivo de metadata del backup
    metadata = {
        "timestamp": timestamp,
        "fecha_legible": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "descripcion": descripcion,
        "archivos_respaldados": archivos_copiados,
        "carpetas_respaldadas": carpetas_copiadas,
        "estado_bot": "FUNCIONANDO" if Path("bot.pid").exists() else "DETENIDO",
        "capital": "$21,891.65 ARS",
        "version": "2.0"
    }
    
    # Obtener PID si existe
    if Path("bot.pid").exists():
        try:
            with open("bot.pid", 'r') as f:
                metadata["bot_pid"] = f.read().strip()
        except:
            pass
    
    # Guardar metadata
    with open(backup_dir / "BACKUP_INFO.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print("="*70)
    print("✅ BACKUP COMPLETADO")
    print("="*70)
    print(f"📁 Ubicación: {backup_dir}")
    print(f"📊 Archivos: {archivos_copiados}")
    print(f"📂 Carpetas: {carpetas_copiadas}")
    print(f"📅 Fecha: {metadata['fecha_legible']}")
    print()
    print("💡 Para restaurar este backup:")
    print(f"   python restaurar_backup.py {backup_name}")
    print()
    
    return backup_dir

if __name__ == "__main__":
    import sys
    descripcion = sys.argv[1] if len(sys.argv) > 1 else "pre_desarrollo"
    crear_backup(descripcion)

