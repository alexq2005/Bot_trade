"""
Script para Restaurar un Backup
"""
import shutil
import sys
import json
from pathlib import Path

def listar_backups():
    """Lista todos los backups disponibles"""
    backups_dir = Path("backups")
    if not backups_dir.exists():
        print("❌ No hay backups disponibles")
        return []
    
    backups = sorted(backups_dir.glob("stable_*"), key=lambda x: x.stat().st_mtime, reverse=True)
    return backups

def restaurar_backup(backup_name):
    """Restaura un backup específico"""
    backup_dir = Path(f"backups/{backup_name}")
    
    if not backup_dir.exists():
        print(f"❌ Backup no encontrado: {backup_name}")
        return False
    
    print("="*70)
    print("⚠️  RESTAURANDO BACKUP")
    print("="*70)
    print(f"📁 Desde: {backup_dir}")
    print()
    
    # Leer metadata
    metadata_file = backup_dir / "BACKUP_INFO.json"
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        print(f"📅 Backup de: {metadata.get('fecha_legible', 'N/A')}")
        print(f"📝 Descripción: {metadata.get('descripcion', 'N/A')}")
        print(f"📊 Archivos: {metadata.get('archivos_respaldados', '?')}")
        print()
    
    # Confirmar
    respuesta = input("⚠️  ¿CONFIRMAS que quieres SOBRESCRIBIR el estado actual? (yes/no): ")
    if respuesta.lower() != 'yes':
        print("❌ Restauración cancelada")
        return False
    
    print()
    print("🔄 Restaurando archivos...")
    
    # Restaurar archivos individuales
    for archivo in backup_dir.glob("*.py"):
        try:
            shutil.copy(archivo, archivo.name)
            print(f"  ✅ {archivo.name}")
        except Exception as e:
            print(f"  ❌ {archivo.name}: {e}")
    
    for archivo in backup_dir.glob("*.json"):
        try:
            shutil.copy(archivo, archivo.name)
            print(f"  ✅ {archivo.name}")
        except Exception as e:
            print(f"  ❌ {archivo.name}: {e}")
    
    # Restaurar carpetas
    for carpeta in ['src', 'scripts', 'tests', 'config', 'models']:
        carpeta_backup = backup_dir / carpeta
        if carpeta_backup.exists():
            try:
                if Path(carpeta).exists():
                    shutil.rmtree(carpeta)
                shutil.copytree(carpeta_backup, carpeta)
                print(f"  ✅ {carpeta}/")
            except Exception as e:
                print(f"  ❌ {carpeta}/: {e}")
    
    print()
    print("="*70)
    print("✅ BACKUP RESTAURADO")
    print("="*70)
    print("⚠️  Reinicia el bot para aplicar cambios")
    print()
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("📋 Backups disponibles:")
        print()
        backups = listar_backups()
        if backups:
            for i, backup in enumerate(backups, 1):
                print(f"  {i}. {backup.name}")
                # Leer metadata si existe
                metadata_file = backup / "BACKUP_INFO.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        print(f"     📅 {metadata.get('fecha_legible', 'N/A')}")
                        print(f"     📝 {metadata.get('descripcion', 'N/A')}")
                    except:
                        pass
                print()
            print()
            print("💡 Uso: python restaurar_backup.py [nombre_backup]")
        else:
            print("  (No hay backups disponibles)")
    else:
        backup_name = sys.argv[1]
        restaurar_backup(backup_name)

