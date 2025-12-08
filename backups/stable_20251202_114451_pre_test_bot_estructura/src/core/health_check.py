"""
Sistema de Health Checks
Verifica el estado de todos los componentes del sistema
"""
from datetime import datetime
from typing import Dict, List, Optional

from src.core.config_manager import get_config
from src.core.logger import get_logger

logger = get_logger("health")


class HealthCheck:
    """Sistema de verificación de salud del sistema"""
    
    def __init__(self):
        self.checks: List[Dict] = []
    
    def check_database(self) -> Dict[str, any]:
        """Verifica el estado de la base de datos"""
        try:
            from src.core.database import SessionLocal, engine
            from src.models.market_data import MarketData
            
            # Verificar conexión
            db = SessionLocal()
            try:
                count = db.query(MarketData).count()
                db.close()
                
                return {
                    'status': 'healthy',
                    'message': f'Base de datos conectada ({count} registros)',
                    'details': {'record_count': count}
                }
            except Exception as e:
                db.close()
                return {
                    'status': 'unhealthy',
                    'message': f'Error consultando base de datos: {e}',
                    'details': {'error': str(e)}
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Error conectando a base de datos: {e}',
                'details': {'error': str(e)}
            }
    
    def check_iol_connection(self) -> Dict[str, any]:
        """Verifica la conexión con IOL"""
        try:
            from src.connectors.iol_client import IOLClient
            
            client = IOLClient()
            account = client.get_account_status()
            
            return {
                'status': 'healthy',
                'message': 'Conexión IOL activa',
                'details': account
            }
        except Exception as e:
            return {
                'status': 'degraded',
                'message': f'Conexión IOL no disponible: {e}',
                'details': {'error': str(e)}
            }
    
    def check_models(self) -> Dict[str, any]:
        """Verifica la disponibilidad de modelos entrenados"""
        try:
            from pathlib import Path
            
            models_dir = Path("models")
            if not models_dir.exists():
                return {
                    'status': 'unhealthy',
                    'message': 'Directorio de modelos no existe',
                    'details': {}
                }
            
            model_files = list(models_dir.glob("*_model.h5"))
            
            if not model_files:
                return {
                    'status': 'degraded',
                    'message': 'No se encontraron modelos entrenados',
                    'details': {'model_count': 0}
                }
            
            return {
                'status': 'healthy',
                'message': f'{len(model_files)} modelos disponibles',
                'details': {'model_count': len(model_files), 'models': [f.name for f in model_files[:5]]}
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Error verificando modelos: {e}',
                'details': {'error': str(e)}
            }
    
    def check_disk_space(self) -> Dict[str, any]:
        """Verifica el espacio en disco"""
        try:
            import shutil
            
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)
            free_pct = (free / total) * 100
            
            status = 'healthy'
            if free_pct < 10:
                status = 'critical'
            elif free_pct < 20:
                status = 'warning'
            
            return {
                'status': status,
                'message': f'{free_gb:.2f} GB libres de {total_gb:.2f} GB ({free_pct:.1f}%)',
                'details': {
                    'free_gb': free_gb,
                    'total_gb': total_gb,
                    'free_percent': free_pct
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Error verificando espacio en disco: {e}',
                'details': {'error': str(e)}
            }
    
    def check_logs(self) -> Dict[str, any]:
        """Verifica el sistema de logs"""
        try:
            from pathlib import Path
            
            logs_dir = Path("logs")
            if not logs_dir.exists():
                return {
                    'status': 'degraded',
                    'message': 'Directorio de logs no existe',
                    'details': {}
                }
            
            log_files = list(logs_dir.glob("*.log"))
            total_size = sum(f.stat().st_size for f in log_files)
            total_size_mb = total_size / (1024**2)
            
            return {
                'status': 'healthy',
                'message': f'{len(log_files)} archivos de log ({total_size_mb:.2f} MB)',
                'details': {
                    'file_count': len(log_files),
                    'total_size_mb': total_size_mb
                }
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Error verificando logs: {e}',
                'details': {'error': str(e)}
            }
    
    def check_config(self) -> Dict[str, any]:
        """Verifica la configuración"""
        try:
            config = get_config()
            
            required_keys = ['app', 'bot', 'database']
            missing = [key for key in required_keys if key not in config]
            
            if missing:
                return {
                    'status': 'degraded',
                    'message': f'Configuración incompleta: faltan {missing}',
                    'details': {'missing_keys': missing}
                }
            
            return {
                'status': 'healthy',
                'message': 'Configuración completa',
                'details': {'sections': list(config.keys())}
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Error verificando configuración: {e}',
                'details': {'error': str(e)}
            }
    
    def run_all_checks(self) -> Dict[str, any]:
        """Ejecuta todas las verificaciones"""
        checks = {
            'database': self.check_database(),
            'models': self.check_models(),
            'disk_space': self.check_disk_space(),
            'logs': self.check_logs(),
            'config': self.check_config(),
            'iol_connection': self.check_iol_connection(),
        }
        
        # Calcular estado general
        statuses = [check['status'] for check in checks.values()]
        if 'unhealthy' in statuses or 'critical' in statuses:
            overall_status = 'unhealthy'
        elif 'degraded' in statuses or 'warning' in statuses:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'checks': checks,
            'summary': {
                'total': len(checks),
                'healthy': sum(1 for s in statuses if s == 'healthy'),
                'degraded': sum(1 for s in statuses if s in ['degraded', 'warning']),
                'unhealthy': sum(1 for s in statuses if s in ['unhealthy', 'critical']),
            }
        }


def get_health_status() -> Dict[str, any]:
    """Función helper para obtener el estado de salud"""
    checker = HealthCheck()
    return checker.run_all_checks()

