"""
Script para crear backup del estado estable
Antes de implementar estructura test_bot/
"""
import shutil
from datetime import datetime
from pathlib import Path
import json

def crear_backup():
    # Crear directorio de backups con timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(f'backups/stable_{timestamp}_pre_test_bot')
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*70)
    print("📦 CREANDO BACKUP DEL ESTADO ESTABLE")
    print("="*70)
    
    # Archivos críticos a respaldar
    archivos_criticos = [
        'trading_bot.py',
        'dashboard.py',
        'run_bot.py',
        'professional_config.json',
        'my_portfolio.json',
        'trades.json'
    ]
    
    # Copiar archivos uno por uno
    copiados = []
    for archivo in archivos_criticos:
        archivo_path = Path(archivo)
        if archivo_path.exists():
            try:
                shutil.copy(archivo, backup_dir / archivo)
                size_kb = archivo_path.stat().st_size / 1024
                print(f"✅ {archivo} ({size_kb:.1f} KB)")
                copiados.append(archivo)
            except Exception as e:
                print(f"❌ Error copiando {archivo}: {e}")
        else:
            print(f"⚠️  {archivo} no existe")
    
    # Copiar carpeta src completa
    src_path = Path('src')
    if src_path.exists():
        try:
            shutil.copytree('src', backup_dir / 'src', dirs_exist_ok=True)
            print(f"✅ src/ (carpeta completa)")
            copiados.append('src/')
        except Exception as e:
            print(f"❌ Error copiando src/: {e}")
    
    # Crear manifest del backup
    manifest = {
        'timestamp': timestamp,
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'descripcion': 'Backup estable antes de crear estructura test_bot/',
        'archivos_respaldados': copiados,
        'capital_actual': 21891.65,
        'version_bot': '2.0',
        'estado': 'PRODUCCION - ESTABLE'
    }
    
    manifest_path = backup_dir / 'MANIFEST.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Manifest creado: MANIFEST.json")
    
    print("\n" + "="*70)
    print(f"✅ BACKUP COMPLETADO")
    print("="*70)
    print(f"📂 Ubicación: {backup_dir}")
    print(f"📦 Archivos respaldados: {len(copiados)}")
    print(f"📄 Manifest: {manifest_path}")
    print("="*70)
    
    return backup_dir

if __name__ == "__main__":
    backup_path = crear_backup()
    print(f"\n🎯 Ahora puedes desarrollar en test_bot/ sin riesgo")
    print(f"💾 Backup disponible en: {backup_path}")
