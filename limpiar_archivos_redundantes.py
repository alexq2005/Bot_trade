"""
Script para eliminar archivos redundantes de forma conservadora
Solo elimina archivos que definitivamente no se usan
"""
from pathlib import Path

def main(auto_confirm=False):
    project_root = Path(__file__).parent
    
    # Archivos a eliminar (conservador - solo redundantes confirmados)
    files_to_delete = []
    
    # Scripts de verificación muy específicos (4)
    specific_verification = [
        'verificar_porque_no_ejecuto_ko.py',
        'verificar_position_size_ko.py',
        'verificar_score_30.py',
        'verificar_si_comprara.py',
    ]
    
    # Scripts de diagnóstico redundantes (3)
    redundant_diagnostic = [
        'diagnostico_porque_no_opera.py',
        'diagnostico_porque_no_opera_hoy.py',
        'diagnostico_telegram.py',
        'diagnostico_trading.py',
    ]
    
    # Scripts de test duplicados (5)
    duplicate_tests = [
        'test_telegram.py',
        'test_telegram_simple.py',
        'test_auto_config.py',
        'test_iol_history.py',
        'test_live_purchase.py',
        'test_live_sale.py',
    ]
    
    # Documentación redundante (15)
    redundant_docs = [
        'COMANDOS_TELEGRAM.md',
        'SOLUCION_POWERSHELL.md',
        'CONFIGURACION_COMPLETA.md',
        'VERIFICATION.md',
        'AUTOMATIC_TRADING_GUIDE.md',
        'TELEGRAM_SETUP.md',
        'CLEANUP_REPORT.md',
        'NEWS_API_SETUP.md',
        'AUTOCONFIGURACION.md',
        'BUGFIXES_REPORT.md',
        'DATA_COLLECTION_GUIDE.md',
        'AGREGAR_SIMBOLOS.md',
        'TRAINING_ERRORS_REPORT.md',
        'RESUMEN_TESTEO.md',
        'ESTADO_ANALISIS_BOT.md',
        'INICIAR_BOT_LIVE.md',
        'QUALITY_SUMMARY.md',
        'COMO_REINICIAR_BOT.md',  # Info en COMANDOS_RAPIDOS.txt
    ]
    
    # Scripts adicionales no esenciales
    other_scripts = [
        'check_bot_status.py',  # Puede hacerse desde dashboard
        'check_learning_status.py',  # Puede hacerse desde dashboard
        'check_selected_symbols.py',  # Puede hacerse desde dashboard
        'check_trained_assets.py',  # Puede hacerse desde dashboard
        'check_training_status.py',  # Puede hacerse desde dashboard
        'enviar_mensaje_telegram.py',  # Funcionalidad en servicios
        'telegram_bot_launcher.py',  # No se usa directamente
    ]
    
    all_files = (
        specific_verification +
        redundant_diagnostic +
        duplicate_tests +
        other_scripts
    )
    
    # Agregar archivos .py
    for filename in all_files:
        file_path = project_root / filename
        if file_path.exists():
            files_to_delete.append(file_path)
    
    # Agregar documentación
    for filename in redundant_docs:
        file_path = project_root / filename
        if file_path.exists():
            files_to_delete.append(file_path)
    
    # Mostrar resumen
    print("=" * 70)
    print("  🗑️  ELIMINACIÓN DE ARCHIVOS REDUNDANTES")
    print("=" * 70)
    print()
    print(f"📊 Total de archivos a eliminar: {len(files_to_delete)}")
    print()
    
    if not files_to_delete:
        print("✅ No hay archivos redundantes para eliminar")
        return
    
    print("Archivos a eliminar:")
    print()
    
    # Agrupar por tipo
    py_files = [f for f in files_to_delete if f.suffix == '.py']
    md_files = [f for f in files_to_delete if f.suffix == '.md']
    
    if py_files:
        print(f"📝 Scripts Python ({len(py_files)}):")
        for f in sorted(py_files):
            print(f"   • {f.name}")
        print()
    
    if md_files:
        print(f"📚 Documentación ({len(md_files)}):")
        for f in sorted(md_files):
            print(f"   • {f.name}")
        print()
    
    # Confirmar
    if not auto_confirm:
        print("⚠️  Estos archivos serán eliminados permanentemente.")
        response = input("¿Continuar? (s/n): ").lower()
        
        if response != 's':
            print("❌ Operación cancelada")
            return
    else:
        print("⚠️  Eliminando archivos automáticamente...")
    
    # Eliminar
    print()
    print("🗑️  Eliminando archivos...")
    deleted = 0
    errors = 0
    
    for file_path in files_to_delete:
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
    import sys
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv
    main(auto_confirm=auto_confirm)

