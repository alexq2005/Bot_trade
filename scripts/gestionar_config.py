"""
Script de Utilidad para Gestión de Configuración
Permite cambiar entre entornos, ver configuración, etc.
"""
import sys
import os
from pathlib import Path

# Agregar directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.config_manager import ConfigManager, Environment, get_config_manager
import yaml


def show_config():
    """Muestra la configuración actual"""
    manager = get_config_manager()
    config = manager.get_config()
    
    print("="*70)
    print("📋 CONFIGURACIÓN ACTUAL")
    print("="*70)
    print(f"Entorno: {config.environment}")
    print()
    
    print("Trading:")
    print(f"  Símbolos: {', '.join(config.trading.symbols)}")
    print(f"  Capital inicial: ${config.trading.initial_capital:,.2f}")
    print(f"  Riesgo por trade: {config.trading.risk_per_trade}%")
    print(f"  Stop Loss: {config.trading.stop_loss_percent}%")
    print(f"  Take Profit: {config.trading.take_profit_percent}%")
    print()
    
    print("IOL:")
    print(f"  Usuario: {config.iol.username}")
    print(f"  Ambiente: {config.iol.environment}")
    print()
    
    print("Telegram:")
    print(f"  Habilitado: {config.telegram.enabled}")
    print(f"  Bot Token: {'***' if config.telegram.bot_token else 'No configurado'}")
    print()
    
    print("Modelo:")
    print(f"  Umbral predicción: {config.model.prediction_threshold}%")
    print(f"  Reentrenamiento: cada {config.model.retrain_interval_days} días")
    print(f"  Fallback técnico: {config.model.use_technical_fallback}")
    print()
    
    print("Sistema:")
    print(f"  Logging: {config.logging_level}")
    print(f"  API Port: {config.api_port}")


def change_environment(env_name: str):
    """Cambia el entorno actual"""
    env_map = {
        "dev": Environment.DEVELOPMENT,
        "development": Environment.DEVELOPMENT,
        "prod": Environment.PRODUCTION,
        "production": Environment.PRODUCTION,
        "paper": Environment.PAPER_TRADING,
        "paper_trading": Environment.PAPER_TRADING,
        "test": Environment.TESTING,
        "testing": Environment.TESTING,
    }
    
    env = env_map.get(env_name.lower())
    if not env:
        print(f"❌ Entorno inválido: {env_name}")
        print(f"   Entornos válidos: {', '.join(env_map.keys())}")
        return
    
    # Establecer variable de entorno
    os.environ["ENVIRONMENT"] = env.value
    
    print(f"✅ Entorno cambiado a: {env.value}")
    print("   💡 Reinicia el bot para aplicar los cambios")
    
    # Mostrar nueva configuración
    print()
    show_config()


def edit_config_file(env_name: str = None):
    """Abre el archivo de configuración para editar"""
    manager = get_config_manager()
    env = manager.current_env
    
    if env_name:
        env_map = {
            "dev": Environment.DEVELOPMENT,
            "development": Environment.DEVELOPMENT,
            "prod": Environment.PRODUCTION,
            "production": Environment.PRODUCTION,
            "paper": Environment.PAPER_TRADING,
            "paper_trading": Environment.PAPER_TRADING,
        }
        env = env_map.get(env_name.lower(), env)
    
    config_file = manager.config_dir / f"{env.value}.yaml"
    
    if not config_file.exists():
        print(f"❌ Archivo de configuración no existe: {config_file}")
        print("   💡 Se creará uno por defecto")
        manager._create_default_config(config_file)
    
    print(f"📝 Abriendo: {config_file}")
    print("   💡 Edita el archivo y guarda los cambios")
    
    # Intentar abrir con editor por defecto
    import subprocess
    import platform
    
    try:
        if platform.system() == "Windows":
            os.startfile(str(config_file))
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(config_file)])
        else:  # Linux
            subprocess.run(["xdg-open", str(config_file)])
    except Exception as e:
        print(f"⚠️  No se pudo abrir automáticamente: {e}")
        print(f"   Abre manualmente: {config_file}")


def validate_config():
    """Valida la configuración actual"""
    manager = get_config_manager()
    config = manager.get_config()
    
    errors = []
    warnings = []
    
    # Validar IOL
    if not config.iol.username:
        errors.append("IOL username no configurado")
    if not config.iol.password:
        errors.append("IOL password no configurado")
    
    # Validar Telegram
    if config.telegram.enabled and not config.telegram.bot_token:
        warnings.append("Telegram habilitado pero bot_token no configurado")
    
    # Validar Trading
    if not config.trading.symbols:
        errors.append("No hay símbolos configurados")
    if config.trading.risk_per_trade > 5:
        warnings.append(f"Riesgo por trade muy alto: {config.trading.risk_per_trade}%")
    
    print("="*70)
    print("🔍 VALIDACIÓN DE CONFIGURACIÓN")
    print("="*70)
    
    if errors:
        print("\n❌ ERRORES:")
        for error in errors:
            print(f"   • {error}")
    
    if warnings:
        print("\n⚠️  ADVERTENCIAS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    if not errors and not warnings:
        print("\n✅ Configuración válida")
    
    return len(errors) == 0


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestión de Configuración")
    parser.add_argument("command", choices=["show", "change", "edit", "validate"], help="Comando a ejecutar")
    parser.add_argument("--env", help="Entorno (para change o edit)")
    
    args = parser.parse_args()
    
    if args.command == "show":
        show_config()
    elif args.command == "change":
        if not args.env:
            print("❌ Debes especificar un entorno con --env")
            print("   Ejemplo: python gestionar_config.py change --env development")
            return
        change_environment(args.env)
    elif args.command == "edit":
        edit_config_file(args.env)
    elif args.command == "validate":
        validate_config()


if __name__ == "__main__":
    main()

