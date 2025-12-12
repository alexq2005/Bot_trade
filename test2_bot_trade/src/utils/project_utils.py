"""
Utilidades del Proyecto
Funciones helper para operaciones comunes
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.logger import get_logger

logger = get_logger("utils")


def ensure_dir(path: str | Path) -> Path:
    """Asegura que un directorio exista"""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def load_json(file_path: str | Path, default: Any = None) -> Any:
    """Carga un archivo JSON"""
    path = Path(file_path)
    if not path.exists():
        return default
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando JSON {file_path}: {e}")
        return default


def save_json(data: Any, file_path: str | Path, indent: int = 2) -> bool:
    """Guarda datos en un archivo JSON"""
    path = Path(file_path)
    try:
        ensure_dir(path.parent)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        logger.error(f"Error guardando JSON {file_path}: {e}")
        return False


def format_currency(amount: float, currency: str = "ARS") -> str:
    """Formatea un monto como moneda"""
    if currency == "ARS":
        return f"${amount:,.2f} {currency}"
    return f"{amount:,.2f} {currency}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Formatea un valor como porcentaje"""
    return f"{value:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """Formatea un número con separadores de miles"""
    return f"{value:,.{decimals}f}"


def get_project_root() -> Path:
    """Obtiene la raíz del proyecto"""
    current = Path(__file__).resolve()
    # Subir hasta encontrar el directorio con trading_bot.py
    while current.parent != current:
        if (current / "trading_bot.py").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_data_dir() -> Path:
    """Obtiene el directorio de datos"""
    root = get_project_root()
    data_dir = root / "data"
    ensure_dir(data_dir)
    return data_dir


def get_logs_dir() -> Path:
    """Obtiene el directorio de logs"""
    root = get_project_root()
    logs_dir = root / "logs"
    ensure_dir(logs_dir)
    return logs_dir


def get_models_dir() -> Path:
    """Obtiene el directorio de modelos"""
    root = get_project_root()
    models_dir = root / "models"
    ensure_dir(models_dir)
    return models_dir


def clean_old_files(directory: Path, pattern: str, days: int = 30):
    """Elimina archivos antiguos de un directorio"""
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    deleted_count = 0
    
    for file_path in directory.glob(pattern):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_date:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(f"Eliminado archivo antiguo: {file_path}")
                except Exception as e:
                    logger.warning(f"Error eliminando {file_path}: {e}")
    
    if deleted_count > 0:
        logger.info(f"Eliminados {deleted_count} archivos antiguos de {directory}")
    
    return deleted_count


def get_file_size_mb(file_path: Path) -> float:
    """Obtiene el tamaño de un archivo en MB"""
    if not file_path.exists():
        return 0.0
    return file_path.stat().st_size / (1024 * 1024)


def get_directory_size_mb(directory: Path) -> float:
    """Obtiene el tamaño total de un directorio en MB"""
    total = 0
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            total += file_path.stat().st_size
    return total / (1024 * 1024)


def backup_file(file_path: Path, backup_dir: Optional[Path] = None) -> Path:
    """Crea un backup de un archivo"""
    if backup_dir is None:
        backup_dir = get_project_root() / "backups"
    ensure_dir(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name
    
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backup creado: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Error creando backup: {e}")
        raise


def validate_symbol(symbol: str) -> bool:
    """Valida que un símbolo tenga formato correcto"""
    if not symbol or len(symbol) < 1:
        return False
    
    # Permitir letras, números, puntos y guiones
    allowed_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-')
    return all(c.upper() in allowed_chars for c in symbol)


def parse_symbol(symbol: str) -> tuple[str, Optional[str]]:
    """Parsea un símbolo en (símbolo, mercado)"""
    if '.' in symbol:
        parts = symbol.split('.')
        return parts[0], parts[1] if len(parts) > 1 else None
    return symbol, None


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """División segura que evita división por cero"""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Limita un valor entre min y max"""
    return max(min_val, min(max_val, value))

