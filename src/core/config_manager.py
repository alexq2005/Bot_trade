"""
Sistema de Configuración Mejorado con YAML y Múltiples Entornos
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from src.core.logger import get_logger

logger = get_logger("config_manager")


class Environment(Enum):
    """Entornos disponibles"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    PAPER_TRADING = "paper_trading"
    TESTING = "testing"


@dataclass
class TradingConfig:
    """Configuración de trading"""
    symbols: list
    initial_capital: float
    max_position_size: float
    risk_per_trade: float
    stop_loss_percent: float
    take_profit_percent: float


@dataclass
class IOLConfig:
    """Configuración de IOL"""
    username: str
    password: str
    account_number: str
    environment: str  # 'demo' o 'live'


@dataclass
class TelegramConfig:
    """Configuración de Telegram"""
    bot_token: str
    chat_id: str
    enabled: bool = True


@dataclass
class ModelConfig:
    """Configuración de modelos IA"""
    prediction_threshold: float = 2.0
    model_retrain_interval_days: int = 7
    use_technical_fallback: bool = True


@dataclass
class SystemConfig:
    """Configuración completa del sistema"""
    environment: str
    trading: TradingConfig
    iol: IOLConfig
    telegram: TelegramConfig
    model: ModelConfig
    logging_level: str = "INFO"
    api_port: int = 8000


class ConfigManager:
    """
    Gestor de configuración con soporte para múltiples entornos
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: Directorio donde están los archivos de configuración
        """
        self.config_dir = config_dir or Path("config")
        self.config_dir.mkdir(exist_ok=True)
        
        # Determinar entorno actual
        self.current_env = self._detect_environment()
        self.logger = logger
        
        # Cargar configuración
        self._config: Optional[SystemConfig] = None
        self.load_config()
    
    def _detect_environment(self) -> Environment:
        """Detecta el entorno actual"""
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        
        # Mapear strings a enum
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
        
        return env_map.get(env_str, Environment.DEVELOPMENT)
    
    def load_config(self) -> SystemConfig:
        """
        Carga la configuración del entorno actual
        
        Returns:
            SystemConfig con la configuración cargada
        """
        # Cargar configuración base
        base_config = self._load_yaml("base.yaml")
        
        # Cargar configuración del entorno
        env_config = self._load_yaml(f"{self.current_env.value}.yaml")
        
        # Merge: base + entorno (entorno sobrescribe base)
        merged_config = self._merge_configs(base_config, env_config or {})
        
        # Convertir a SystemConfig
        self._config = self._dict_to_config(merged_config)
        
        self.logger.info(f"Configuración cargada para entorno: {self.current_env.value}")
        
        return self._config
    
    def _load_yaml(self, filename: str) -> Optional[Dict]:
        """Carga un archivo YAML"""
        config_file = self.config_dir / filename
        
        if not config_file.exists():
            # Si no existe, crear uno por defecto
            if filename == "base.yaml":
                self._create_default_config(config_file)
                return self._load_yaml(filename)
            return None
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"Error cargando {filename}: {e}")
            return None
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Fusiona dos configuraciones (override sobrescribe base)"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _dict_to_config(self, config_dict: Dict) -> SystemConfig:
        """Convierte un diccionario a SystemConfig"""
        # Obtener valores de .env si no están en YAML
        trading = TradingConfig(
            symbols=config_dict.get("trading", {}).get("symbols", ["GGAL", "YPFD"]),
            initial_capital=float(config_dict.get("trading", {}).get("initial_capital", 100000.0)),
            max_position_size=float(config_dict.get("trading", {}).get("max_position_size", 10000.0)),
            risk_per_trade=float(config_dict.get("trading", {}).get("risk_per_trade", 2.0)),
            stop_loss_percent=float(config_dict.get("trading", {}).get("stop_loss_percent", 3.0)),
            take_profit_percent=float(config_dict.get("trading", {}).get("take_profit_percent", 6.0)),
        )
        
        iol = IOLConfig(
            username=config_dict.get("iol", {}).get("username") or os.getenv("IOL_USERNAME", ""),
            password=config_dict.get("iol", {}).get("password") or os.getenv("IOL_PASSWORD", ""),
            account_number=config_dict.get("iol", {}).get("account_number") or os.getenv("IOL_ACCOUNT", ""),
            environment=config_dict.get("iol", {}).get("environment", "demo"),
        )
        
        telegram = TelegramConfig(
            bot_token=config_dict.get("telegram", {}).get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN", ""),
            chat_id=config_dict.get("telegram", {}).get("chat_id") or os.getenv("TELEGRAM_CHAT_ID", ""),
            enabled=config_dict.get("telegram", {}).get("enabled", True),
        )
        
        model = ModelConfig(
            prediction_threshold=float(config_dict.get("model", {}).get("prediction_threshold", 2.0)),
            model_retrain_interval_days=int(config_dict.get("model", {}).get("retrain_interval_days", 7)),
            use_technical_fallback=config_dict.get("model", {}).get("use_technical_fallback", True),
        )
        
        return SystemConfig(
            environment=self.current_env.value,
            trading=trading,
            iol=iol,
            telegram=telegram,
            model=model,
            logging_level=config_dict.get("logging_level", "INFO"),
            api_port=int(config_dict.get("api_port", 8000)),
        )
    
    def _create_default_config(self, config_file: Path):
        """Crea un archivo de configuración por defecto"""
        default_config = {
            "trading": {
                "symbols": ["GGAL", "YPFD", "AAPL"],
                "initial_capital": 100000.0,
                "max_position_size": 10000.0,
                "risk_per_trade": 2.0,
                "stop_loss_percent": 3.0,
                "take_profit_percent": 6.0,
            },
            "iol": {
                "username": "",
                "password": "",
                "account_number": "",
                "environment": "demo",
            },
            "telegram": {
                "bot_token": "",
                "chat_id": "",
                "enabled": True,
            },
            "model": {
                "prediction_threshold": 2.0,
                "retrain_interval_days": 7,
                "use_technical_fallback": True,
            },
            "logging_level": "INFO",
            "api_port": 8000,
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        self.logger.info(f"Archivo de configuración por defecto creado: {config_file}")
    
    def get_config(self) -> SystemConfig:
        """Obtiene la configuración actual"""
        if self._config is None:
            self.load_config()
        return self._config
    
    def save_config(self, config: SystemConfig, env: Optional[Environment] = None):
        """
        Guarda la configuración en un archivo YAML
        
        Args:
            config: Configuración a guardar
            env: Entorno (si None, usa el actual)
        """
        env = env or self.current_env
        config_file = self.config_dir / f"{env.value}.yaml"
        
        config_dict = {
            "trading": asdict(config.trading),
            "iol": asdict(config.iol),
            "telegram": asdict(config.telegram),
            "model": asdict(config.model),
            "logging_level": config.logging_level,
            "api_port": config.api_port,
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
        
        self.logger.info(f"Configuración guardada en {config_file}")
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración usando notación de punto
        
        Args:
            key_path: Ruta de la clave (ej: "trading.symbols")
            default: Valor por defecto si no existe
        
        Returns:
            Valor de la configuración
        """
        config = self.get_config()
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = getattr(value, key, None)
            
            if value is None:
                return default
        
        return value


# Instancia global
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Obtiene la instancia global de ConfigManager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> SystemConfig:
    """Obtiene la configuración actual"""
    return get_config_manager().get_config()
