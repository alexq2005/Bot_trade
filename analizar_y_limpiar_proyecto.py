"""
Script para analizar el proyecto, identificar archivos no utilizados y limpiar
"""
import os
import ast
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
import json

class ProjectAnalyzer:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.imports = set()
        self.files_imported = set()
        self.all_py_files = []
        self.file_usage = defaultdict(list)
        self.entry_points = [
            'run_bot.py',
            'dashboard.py',
            'cli.py',
            'start_live_trading.py',
        ]
        
    def get_python_files(self):
        """Obtiene todos los archivos Python del proyecto (excluyendo venv)"""
        py_files = []
        excluded_dirs = {'venv', '__pycache__', '.git', 'node_modules', '.pytest_cache', '.mypy_cache'}
        
        for root, dirs, files in os.walk(self.project_root):
            # Excluir directorios no deseados
            root_path = Path(root)
            if any(excluded in root_path.parts for excluded in excluded_dirs):
                dirs[:] = []  # No explorar subdirectorios
                continue
            
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    py_files.append(file_path)
        
        return py_files
    
    def extract_imports(self, file_path):
        """Extrae todos los imports de un archivo Python"""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
        except Exception as e:
            # Si hay error parseando, intentar método simple
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('import '):
                            module = line.split('import ')[1].split()[0].split('.')[0]
                            imports.append(module)
                        elif line.startswith('from '):
                            parts = line.split('from ')[1].split(' import')[0].strip()
                            module = parts.split('.')[0]
                            imports.append(module)
            except:
                pass
        
        return imports
    
    def find_file_references(self, module_name):
        """Encuentra archivos que podrían corresponder a un módulo"""
        possible_files = []
        
        # Buscar archivo directo
        for py_file in self.all_py_files:
            if py_file.stem == module_name or py_file.name == f"{module_name}.py":
                possible_files.append(py_file)
        
        # Buscar en src/
        src_path = self.project_root / 'src'
        if src_path.exists():
            for root, dirs, files in os.walk(src_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = Path(root) / file
                        if file_path.stem == module_name or file_path.name == f"{module_name}.py":
                            possible_files.append(file_path)
        
        return possible_files
    
    def analyze_project(self):
        """Analiza todo el proyecto"""
        print("=" * 70)
        print("  🔍 ANÁLISIS DEL PROYECTO")
        print("=" * 70)
        print()
        
        # Obtener todos los archivos Python
        print("📂 Buscando archivos Python (excluyendo venv)...")
        self.all_py_files = self.get_python_files()
        # Filtrar solo archivos del proyecto (no venv)
        self.all_py_files = [f for f in self.all_py_files if 'venv' not in str(f)]
        print(f"   Encontrados: {len(self.all_py_files)} archivos")
        print()
        
        # Analizar imports de archivos principales
        print("📊 Analizando imports de archivos principales...")
        main_files = [f for f in self.all_py_files if f.name in self.entry_points]
        
        all_imports = set()
        for file_path in main_files:
            print(f"   Analizando: {file_path.name}")
            imports = self.extract_imports(file_path)
            all_imports.update(imports)
            self.file_usage[file_path] = imports
        
        # Analizar todos los archivos en src/
        print()
        print("📊 Analizando archivos en src/...")
        src_files = [f for f in self.all_py_files if 'src' in str(f)]
        for file_path in src_files:
            imports = self.extract_imports(file_path)
            all_imports.update(imports)
            self.file_usage[file_path] = imports
        
        self.imports = all_imports
        print(f"   Módulos únicos importados: {len(all_imports)}")
        print()
        
        return all_imports
    
    def find_unused_files(self):
        """Encuentra archivos que no se usan"""
        print("=" * 70)
        print("  🗑️  IDENTIFICANDO ARCHIVOS NO UTILIZADOS")
        print("=" * 70)
        print()
        
        # Archivos que definitivamente se usan
        used_files = set()
        
        # Archivos de entrada
        for entry in self.entry_points:
            entry_file = self.project_root / entry
            if entry_file.exists():
                used_files.add(entry_file)
        
        # Archivos en src/ que se importan
        for file_path in self.all_py_files:
            if 'src' in str(file_path):
                # Verificar si se importa desde algún lugar
                module_name = file_path.stem
                # Buscar referencias
                for other_file, imports in self.file_usage.items():
                    if module_name in imports or file_path.name in str(other_file):
                        used_files.add(file_path)
                        break
        
        # Archivos de scripts de utilidad que pueden ser llamados directamente
        utility_scripts = [
            'verificar_instalacion.py',
            'testeo_completo.py',
            'migrar_python.py',
            'activar_venv_310.py',
            'crear_venv_310.py',
        ]
        
        for script in utility_scripts:
            script_file = self.project_root / script
            if script_file.exists():
                used_files.add(script_file)
        
        # Identificar archivos no usados
        unused_files = []
        for file_path in self.all_py_files:
            # Excluir archivos de test y scripts de utilidad
            if file_path not in used_files:
                # Verificar si es un script de verificación/diagnóstico
                name = file_path.name.lower()
                if any(keyword in name for keyword in ['verificar', 'diagnostico', 'test', 'check', 'monitorear']):
                    # Estos pueden ser útiles aunque no se importen
                    continue
                
                # Verificar si está en src/ y no se importa
                if 'src' in str(file_path):
                    # Verificar si realmente se importa
                    module_path = str(file_path.relative_to(self.project_root)).replace('\\', '/').replace('.py', '').replace('/', '.')
                    is_imported = False
                    for other_file, imports in self.file_usage.items():
                        if any(module_path in imp or file_path.stem in imp for imp in imports):
                            is_imported = True
                            break
                    
                    if not is_imported:
                        unused_files.append(file_path)
                elif file_path.parent == self.project_root:
                    # Archivo en raíz que no es punto de entrada
                    if file_path.name not in self.entry_points and file_path.name not in utility_scripts:
                        unused_files.append(file_path)
        
        return unused_files
    
    def find_duplicate_docs(self):
        """Encuentra documentación duplicada o redundante"""
        print("=" * 70)
        print("  📚 IDENTIFICANDO DOCUMENTACIÓN REDUNDANTE")
        print("=" * 70)
        print()
        
        doc_files = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules']]
            for file in files:
                if file.endswith(('.md', '.txt')):
                    doc_files.append(Path(root) / file)
        
        # Agrupar por tema similar
        doc_groups = defaultdict(list)
        for doc_file in doc_files:
            name_lower = doc_file.stem.lower()
            # Agrupar por palabras clave
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
        
        redundant = []
        for group, files in doc_groups.items():
            if len(files) > 2:  # Si hay más de 2 archivos sobre el mismo tema
                # Mantener los más importantes, marcar otros como potencialmente redundantes
                files_sorted = sorted(files, key=lambda x: x.stat().st_size, reverse=True)
                redundant.extend(files_sorted[2:])  # Mantener solo los 2 más grandes
        
        return redundant
    
    def run_tests(self):
        """Ejecuta tests del proyecto"""
        print("=" * 70)
        print("  🧪 EJECUTANDO TESTS")
        print("=" * 70)
        print()
        
        test_results = {}
        
        # Test 1: Verificar instalación
        print("1. Verificando instalación...")
        try:
            result = subprocess.run(
                [sys.executable, 'verificar_instalacion.py'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            test_results['instalacion'] = result.returncode == 0
            if result.returncode == 0:
                print("   ✅ Instalación OK")
            else:
                print("   ❌ Error en instalación")
                print(f"   {result.stderr[:200]}")
        except Exception as e:
            test_results['instalacion'] = False
            print(f"   ❌ Error: {e}")
        
        print()
        
        # Test 2: Testeo completo
        print("2. Ejecutando testeo completo...")
        try:
            result = subprocess.run(
                [sys.executable, 'testeo_completo.py'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            test_results['testeo_completo'] = result.returncode == 0
            if result.returncode == 0:
                print("   ✅ Testeo completo OK")
            else:
                print("   ⚠️  Algunos tests fallaron")
        except Exception as e:
            test_results['testeo_completo'] = False
            print(f"   ❌ Error: {e}")
        
        print()
        
        return test_results
    
    def generate_report(self, unused_files, redundant_docs, test_results):
        """Genera un reporte completo"""
        print("=" * 70)
        print("  📋 REPORTE COMPLETO")
        print("=" * 70)
        print()
        
        print(f"📊 Estadísticas:")
        print(f"   • Archivos Python totales: {len(self.all_py_files)}")
        print(f"   • Archivos no utilizados: {len(unused_files)}")
        print(f"   • Documentación redundante: {len(redundant_docs)}")
        print()
        
        if unused_files:
            print("🗑️  Archivos Python no utilizados:")
            for file_path in sorted(unused_files):
                rel_path = file_path.relative_to(self.project_root)
                print(f"   • {rel_path}")
            print()
        
        if redundant_docs:
            print("📚 Documentación potencialmente redundante:")
            for doc_file in sorted(redundant_docs):
                rel_path = doc_file.relative_to(self.project_root)
                print(f"   • {rel_path}")
            print()
        
        print("🧪 Resultados de tests:")
        for test_name, passed in test_results.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {test_name}")
        print()
        
        # Guardar reporte
        report = {
            'unused_files': [str(f.relative_to(self.project_root)) for f in unused_files],
            'redundant_docs': [str(f.relative_to(self.project_root)) for f in redundant_docs],
            'test_results': test_results,
            'total_files': len(self.all_py_files),
        }
        
        report_file = self.project_root / 'limpieza_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Reporte guardado en: {report_file}")
        print()
        
        return report

def main():
    project_root = Path(__file__).parent
    
    analyzer = ProjectAnalyzer(project_root)
    
    # Analizar proyecto
    analyzer.analyze_project()
    print()
    
    # Encontrar archivos no usados
    unused_files = analyzer.find_unused_files()
    print()
    
    # Encontrar documentación redundante
    redundant_docs = analyzer.find_duplicate_docs()
    print()
    
    # Ejecutar tests
    test_results = analyzer.run_tests()
    print()
    
    # Generar reporte
    report = analyzer.generate_report(unused_files, redundant_docs, test_results)
    
    # Preguntar si eliminar
    print("=" * 70)
    print("  🗑️  ELIMINACIÓN DE ARCHIVOS")
    print("=" * 70)
    print()
    
    if unused_files or redundant_docs:
        print("⚠️  Se encontraron archivos que podrían eliminarse.")
        print()
        print("Archivos a eliminar:")
        for file_path in unused_files + redundant_docs:
            rel_path = file_path.relative_to(project_root)
            print(f"   • {rel_path}")
        print()
        
        response = input("¿Deseas eliminar estos archivos? (s/n): ").lower()
        if response == 's':
            deleted = 0
            for file_path in unused_files + redundant_docs:
                try:
                    file_path.unlink()
                    print(f"   ✅ Eliminado: {file_path.name}")
                    deleted += 1
                except Exception as e:
                    print(f"   ❌ Error eliminando {file_path.name}: {e}")
            
            print()
            print(f"✅ {deleted} archivos eliminados")
        else:
            print("❌ Operación cancelada")
    else:
        print("✅ No se encontraron archivos para eliminar")

if __name__ == "__main__":
    main()

