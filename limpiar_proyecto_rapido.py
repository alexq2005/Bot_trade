"""
Script rápido para identificar y eliminar archivos no utilizados
Versión optimizada que solo analiza archivos del proyecto (no venv)
"""
import os
from pathlib import Path
import json

def get_project_files(project_root):
    """Obtiene solo archivos del proyecto (excluyendo venv, __pycache__, etc.)"""
    project_root = Path(project_root)
    files = []
    
    excluded_dirs = {'venv', '__pycache__', '.git', 'node_modules', '.pytest_cache'}
    excluded_files = {'analizar_y_limpiar_proyecto.py', 'limpiar_proyecto_rapido.py'}
    
    for root, dirs, filenames in os.walk(project_root):
        root_path = Path(root)
        
        # Saltar si está en un directorio excluido
        if any(excluded in root_path.parts for excluded in excluded_dirs):
            dirs[:] = []
            continue
        
        # Filtrar directorios
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for filename in filenames:
            if filename in excluded_files:
                continue
            file_path = root_path / filename
            files.append(file_path)
    
    return files

def identify_unused_scripts():
    """Identifica scripts de verificación/diagnóstico que pueden ser redundantes"""
    project_root = Path(__file__).parent
    
    # Scripts principales que SÍ se usan
    essential_scripts = {
        'run_bot.py',
        'dashboard.py',
        'trading_bot.py',
        'cli.py',
        'testeo_completo.py',
        'verificar_instalacion.py',
        'migrar_python.py',
        'activar_venv_310.py',
        'crear_venv_310.py',
    }
    
    # Scripts de verificación que pueden ser redundantes
    verification_scripts = []
    for file_path in project_root.glob('verificar_*.py'):
        if file_path.name not in essential_scripts:
            verification_scripts.append(file_path)
    
    # Scripts de diagnóstico que pueden ser redundantes
    diagnostic_scripts = []
    for file_path in project_root.glob('diagnostico_*.py'):
        diagnostic_scripts.append(file_path)
    
    # Scripts de test que pueden ser redundantes
    test_scripts = []
    for file_path in project_root.glob('test_*.py'):
        if file_path.name not in essential_scripts:
            test_scripts.append(file_path)
    
    return verification_scripts, diagnostic_scripts, test_scripts

def identify_redundant_docs():
    """Identifica documentación redundante"""
    project_root = Path(__file__).parent
    
    # Documentación esencial
    essential_docs = {
        'README.md',
        'GUIA_INSTALACION.md',
        'COMANDOS_RAPIDOS.txt',
        'requirements.txt',
    }
    
    # Agrupar por tema
    doc_groups = {
        'instalacion': [],
        'comandos': [],
        'migracion': [],
        'mejoras': [],
        'soluciones': [],
        'otros': [],
    }
    
    for doc_file in project_root.glob('*.md'):
        if doc_file.name in essential_docs:
            continue
        
        name_lower = doc_file.stem.lower()
        if 'instalacion' in name_lower or 'install' in name_lower:
            doc_groups['instalacion'].append(doc_file)
        elif 'comando' in name_lower or 'command' in name_lower:
            doc_groups['comandos'].append(doc_file)
        elif 'migracion' in name_lower or 'migration' in name_lower:
            doc_groups['migracion'].append(doc_file)
        elif 'mejora' in name_lower or 'improvement' in name_lower:
            doc_groups['mejoras'].append(doc_file)
        elif 'solucion' in name_lower or 'solution' in name_lower:
            doc_groups['soluciones'].append(doc_file)
        else:
            doc_groups['otros'].append(doc_file)
    
    # Identificar redundantes (más de 2 archivos sobre el mismo tema)
    redundant = []
    for group, files in doc_groups.items():
        if len(files) > 2:
            # Mantener los 2 más grandes, marcar otros como redundantes
            files_sorted = sorted(files, key=lambda x: x.stat().st_size, reverse=True)
            redundant.extend(files_sorted[2:])
    
    return redundant

def main():
    print("=" * 70)
    print("  🧹 LIMPIEZA RÁPIDA DEL PROYECTO")
    print("=" * 70)
    print()
    
    project_root = Path(__file__).parent
    
    # Identificar archivos
    print("🔍 Identificando archivos...")
    verification, diagnostic, test = identify_unused_scripts()
    redundant_docs = identify_redundant_docs()
    
    print()
    print("=" * 70)
    print("  📋 ARCHIVOS IDENTIFICADOS")
    print("=" * 70)
    print()
    
    all_to_delete = []
    
    if verification:
        print(f"📝 Scripts de verificación ({len(verification)}):")
        for f in verification:
            print(f"   • {f.name}")
            all_to_delete.append(f)
        print()
    
    if diagnostic:
        print(f"🔍 Scripts de diagnóstico ({len(diagnostic)}):")
        for f in diagnostic:
            print(f"   • {f.name}")
            all_to_delete.append(f)
        print()
    
    if test:
        print(f"🧪 Scripts de test ({len(test)}):")
        for f in test:
            print(f"   • {f.name}")
            all_to_delete.append(f)
        print()
    
    if redundant_docs:
        print(f"📚 Documentación redundante ({len(redundant_docs)}):")
        for f in redundant_docs:
            print(f"   • {f.name}")
            all_to_delete.append(f)
        print()
    
    if not all_to_delete:
        print("✅ No se encontraron archivos redundantes para eliminar")
        return
    
    print(f"📊 Total de archivos a eliminar: {len(all_to_delete)}")
    print()
    
    # Preguntar confirmación
    print("⚠️  Estos archivos serán eliminados permanentemente.")
    response = input("¿Continuar? (s/n): ").lower()
    
    if response != 's':
        print("❌ Operación cancelada")
        return
    
    # Eliminar archivos
    print()
    print("🗑️  Eliminando archivos...")
    deleted = 0
    errors = 0
    
    for file_path in all_to_delete:
        try:
            file_path.unlink()
            print(f"   ✅ {file_path.name}")
            deleted += 1
        except Exception as e:
            print(f"   ❌ Error eliminando {file_path.name}: {e}")
            errors += 1
    
    print()
    print("=" * 70)
    print(f"  ✅ LIMPIEZA COMPLETADA")
    print("=" * 70)
    print(f"   • Eliminados: {deleted}")
    print(f"   • Errores: {errors}")
    print()

if __name__ == "__main__":
    main()

