"""
Script para Organizar Archivos del Proyecto
Mueve archivos sueltos a directorios apropiados
"""
import shutil
from pathlib import Path
from datetime import datetime

# Mapeo de archivos a directorios
FILE_ORGANIZATION = {
    'debug_*.py': 'scripts/debug/',
    'test_*.py': 'tests/',
    'check_*.py': 'scripts/utils/',
    'quick_*.py': 'scripts/utils/',
    'ver_*.py': 'scripts/utils/',
    '*.log': 'logs/',
    '*.txt': 'logs/',
    '*.json': 'data/',
    '*.csv': 'data/',
    '*.png': 'assets/images/',
    '*.jpg': 'assets/images/',
    '*.pdf': 'docs/',
    '*.md': 'docs/',
    '*.html': 'data/html/',
    '*.db': 'data/databases/',
    '*.h5': 'models/',
    '*.pkl': 'models/',
    '*.pid': 'data/',
}

# Archivos que NO deben moverse
EXCLUDE_FILES = {
    'trading_bot.py',
    'dashboard.py',
    'cli.py',
    'requirements.txt',
    'pyproject.toml',
    'README.md',
    'VERIFICATION.md',
    'FINAL_SUMMARY.md',
    'QUALITY_SUMMARY.md',
    'bot_config.json',
    '.env',
    '.gitignore',
}


def organize_files(dry_run=True):
    """Organiza archivos en directorios apropiados"""
    base_dir = Path('.')
    moved_count = 0
    created_dirs = set()
    
    print(f"\n{'='*70}")
    print(f"📁 Organizando Archivos del Proyecto")
    print(f"{'='*70}\n")
    
    if dry_run:
        print("🔍 Modo DRY RUN - No se moverán archivos\n")
    
    # Crear directorios necesarios
    for target_dir in FILE_ORGANIZATION.values():
        target_path = base_dir / target_dir
        if not target_path.exists():
            if not dry_run:
                target_path.mkdir(parents=True, exist_ok=True)
            created_dirs.add(target_dir)
            print(f"📂 Creando directorio: {target_dir}")
    
    # Organizar archivos
    for pattern, target_dir in FILE_ORGANIZATION.items():
        # Convertir patrón glob a búsqueda
        if pattern.startswith('*.'):
            extension = pattern[1:]
            files = list(base_dir.glob(f'*{extension}'))
        elif '*' in pattern:
            # Patrón como debug_*.py
            files = list(base_dir.glob(pattern))
        else:
            continue
        
        for file_path in files:
            # Verificar que no esté en la lista de exclusión
            if file_path.name in EXCLUDE_FILES:
                continue
            
            # Verificar que sea un archivo (no directorio)
            if not file_path.is_file():
                continue
            
            target_path = base_dir / target_dir / file_path.name
            
            # Evitar sobrescribir
            if target_path.exists():
                # Agregar timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                stem = file_path.stem
                suffix = file_path.suffix
                new_name = f"{stem}_{timestamp}{suffix}"
                target_path = base_dir / target_dir / new_name
            
            if dry_run:
                print(f"  📄 {file_path.name} → {target_dir}")
            else:
                try:
                    shutil.move(str(file_path), str(target_path))
                    print(f"  ✅ {file_path.name} → {target_dir}")
                    moved_count += 1
                except Exception as e:
                    print(f"  ❌ Error moviendo {file_path.name}: {e}")
    
    print(f"\n{'='*70}")
    if dry_run:
        print(f"🔍 DRY RUN completado - {moved_count} archivos se moverían")
        print(f"💡 Ejecuta con --execute para mover archivos realmente")
    else:
        print(f"✅ Organización completada - {moved_count} archivos movidos")
    print(f"{'='*70}\n")
    
    return moved_count


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Organizar archivos del proyecto')
    parser.add_argument('--execute', action='store_true', 
                       help='Ejecutar realmente (por defecto es dry-run)')
    
    args = parser.parse_args()
    organize_files(dry_run=not args.execute)

