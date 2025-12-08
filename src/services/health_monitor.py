"""
Sistema de Monitoreo de Salud del Bot
Verifica el estado de todos los componentes críticos
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.logger import get_logger
from src.connectors.iol_client import IOLClient

logger = get_logger("health_monitor")


@dataclass
class HealthStatus:
    """Estado de salud de un componente"""
    component: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    message: str
    last_check: datetime
    response_time_ms: Optional[float] = None
    details: Optional[Dict] = None


@dataclass
class SystemHealth:
    """Estado de salud general del sistema"""
    overall_status: str
    timestamp: datetime
    components: List[HealthStatus]
    metrics: Dict
    recommendations: List[str]


class HealthMonitor:
    """
    Monitorea la salud de todos los componentes del sistema de trading
    """
    
    def __init__(self, iol_client: Optional[IOLClient] = None):
        """
        Args:
            iol_client: Cliente IOL opcional (se crea uno si no se proporciona)
        """
        self.iol_client = iol_client
        self.logger = logger
        self._last_health_check = None
        self._health_history = []
    
    def check_all(self) -> SystemHealth:
        """
        Verifica la salud de todos los componentes
        
        Returns:
            SystemHealth con el estado completo del sistema
        """
        components = []
        start_time = datetime.now()
        
        # 1. Verificar bot status
        bot_status = self.check_bot_status()
        components.append(bot_status)
        
        # 2. Verificar conexión IOL
        iol_status = self.check_iol_connection()
        components.append(iol_status)
        
        # 3. Verificar modelos IA
        models_status = self.check_models_health()
        components.append(models_status)
        
        # 4. Verificar base de datos
        db_status = self.check_database_health()
        components.append(db_status)
        
        # 5. Verificar Telegram
        telegram_status = self.check_telegram_connection()
        components.append(telegram_status)
        
        # 6. Verificar sistema de archivos
        filesystem_status = self.check_filesystem_health()
        components.append(filesystem_status)
        
        # Calcular estado general
        unhealthy_count = sum(1 for c in components if c.status == 'unhealthy')
        degraded_count = sum(1 for c in components if c.status == 'degraded')
        
        if unhealthy_count > 0:
            overall_status = 'unhealthy'
        elif degraded_count > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        # Calcular métricas
        total_time = (datetime.now() - start_time).total_seconds() * 1000
        metrics = {
            'total_check_time_ms': total_time,
            'components_checked': len(components),
            'healthy_components': sum(1 for c in components if c.status == 'healthy'),
            'degraded_components': degraded_count,
            'unhealthy_components': unhealthy_count
        }
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(components)
        
        health = SystemHealth(
            overall_status=overall_status,
            timestamp=datetime.now(),
            components=components,
            metrics=metrics,
            recommendations=recommendations
        )
        
        self._last_health_check = health
        self._health_history.append(health)
        
        # Mantener solo últimos 100 checks
        if len(self._health_history) > 100:
            self._health_history = self._health_history[-100:]
        
        return health
    
    def check_bot_status(self) -> HealthStatus:
        """Verifica el estado del bot"""
        start_time = datetime.now()
        
        try:
            pid_file = Path("bot.pid")
            if pid_file.exists():
                # Verificar que el proceso esté corriendo
                import psutil
                try:
                    with open(pid_file, 'r') as f:
                        pid = int(f.read().strip())
                    
                    if psutil.pid_exists(pid):
                        process = psutil.Process(pid)
                        if process.is_running():
                            response_time = (datetime.now() - start_time).total_seconds() * 1000
                            return HealthStatus(
                                component="trading_bot",
                                status="healthy",
                                message="Bot está corriendo",
                                last_check=datetime.now(),
                                response_time_ms=response_time,
                                details={"pid": pid, "cpu_percent": process.cpu_percent(), "memory_mb": process.memory_info().rss / 1024 / 1024}
                            )
                        else:
                            return HealthStatus(
                                component="trading_bot",
                                status="unhealthy",
                                message="Proceso del bot no está corriendo",
                                last_check=datetime.now()
                            )
                    else:
                        return HealthStatus(
                            component="trading_bot",
                            status="unhealthy",
                            message="PID del bot no existe",
                            last_check=datetime.now()
                        )
                except ImportError:
                    # psutil no disponible, solo verificar archivo
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    return HealthStatus(
                        component="trading_bot",
                        status="degraded",
                        message="Bot PID existe pero no se puede verificar proceso (psutil no disponible)",
                        last_check=datetime.now(),
                        response_time_ms=response_time
                    )
            else:
                return HealthStatus(
                    component="trading_bot",
                    status="unhealthy",
                    message="Bot no está corriendo (no hay archivo PID)",
                    last_check=datetime.now()
                )
        except Exception as e:
            return HealthStatus(
                component="trading_bot",
                status="unhealthy",
                message=f"Error verificando bot: {str(e)}",
                last_check=datetime.now()
            )
    
    def check_iol_connection(self) -> HealthStatus:
        """Verifica la conexión con IOL"""
        start_time = datetime.now()
        
        try:
            if not self.iol_client:
                self.iol_client = IOLClient()
            
            # Intentar obtener saldo (operación ligera)
            balance = self.iol_client.get_available_balance()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if balance is not None and balance >= 0:
                return HealthStatus(
                    component="iol_connection",
                    status="healthy",
                    message=f"Conexión a IOL OK. Saldo: ${balance:,.2f}",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details={"balance": balance}
                )
            else:
                return HealthStatus(
                    component="iol_connection",
                    status="degraded",
                    message="Conexión a IOL OK pero saldo no disponible",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return HealthStatus(
                component="iol_connection",
                status="unhealthy",
                message=f"Error conectando a IOL: {str(e)}",
                last_check=datetime.now(),
                response_time_ms=response_time
            )
    
    def check_models_health(self) -> HealthStatus:
        """Verifica el estado de los modelos de IA"""
        start_time = datetime.now()
        
        try:
            models_dir = Path("models")
            if not models_dir.exists():
                return HealthStatus(
                    component="ai_models",
                    status="degraded",
                    message="Directorio de modelos no existe",
                    last_check=datetime.now()
                )
            
            model_files = list(models_dir.glob("*_model.h5"))
            scaler_files = list(models_dir.glob("*_scaler.pkl"))
            
            if len(model_files) == 0:
                return HealthStatus(
                    component="ai_models",
                    status="degraded",
                    message="No hay modelos entrenados",
                    last_check=datetime.now()
                )
            
            # Verificar que los modelos no estén corruptos (tamaño > 0)
            corrupted = []
            for model_file in model_files:
                if model_file.stat().st_size == 0:
                    corrupted.append(model_file.name)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if corrupted:
                return HealthStatus(
                    component="ai_models",
                    status="degraded",
                    message=f"{len(corrupted)} modelos corruptos",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details={"total_models": len(model_files), "corrupted": corrupted}
                )
            else:
                return HealthStatus(
                    component="ai_models",
                    status="healthy",
                    message=f"{len(model_files)} modelos disponibles",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details={"total_models": len(model_files), "total_scalers": len(scaler_files)}
                )
        except Exception as e:
            return HealthStatus(
                component="ai_models",
                status="unhealthy",
                message=f"Error verificando modelos: {str(e)}",
                last_check=datetime.now()
            )
    
    def check_database_health(self) -> HealthStatus:
        """Verifica el estado de la base de datos"""
        start_time = datetime.now()
        
        try:
            db_file = Path("trading_bot.db")
            if not db_file.exists():
                return HealthStatus(
                    component="database",
                    status="degraded",
                    message="Base de datos no existe",
                    last_check=datetime.now()
                )
            
            # Verificar que el archivo no esté corrupto (tamaño > 0)
            db_size = db_file.stat().st_size
            if db_size == 0:
                return HealthStatus(
                    component="database",
                    status="unhealthy",
                    message="Base de datos está vacía o corrupta",
                    last_check=datetime.now()
                )
            
            # Intentar conectar y hacer una query simple
            try:
                from src.core.database import get_db_connection
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM market_data LIMIT 1")
                count = cursor.fetchone()[0]
                conn.close()
                
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                
                return HealthStatus(
                    component="database",
                    status="healthy",
                    message=f"Base de datos OK. {count} registros en market_data",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details={"size_mb": db_size / 1024 / 1024, "records": count}
                )
            except Exception as e:
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                return HealthStatus(
                    component="database",
                    status="degraded",
                    message=f"Base de datos existe pero error al consultar: {str(e)}",
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
        except Exception as e:
            return HealthStatus(
                component="database",
                status="unhealthy",
                message=f"Error verificando base de datos: {str(e)}",
                last_check=datetime.now()
            )
    
    def check_telegram_connection(self) -> HealthStatus:
        """Verifica la conexión con Telegram"""
        start_time = datetime.now()
        
        try:
            from src.services.telegram_bot import TelegramAlertBot
            
            bot = TelegramAlertBot()
            # Verificar que las credenciales estén configuradas
            if not bot.bot_token:
                return HealthStatus(
                    component="telegram",
                    status="degraded",
                    message="Token de Telegram no configurado",
                    last_check=datetime.now()
                )
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return HealthStatus(
                component="telegram",
                status="healthy",
                message="Telegram configurado correctamente",
                last_check=datetime.now(),
                response_time_ms=response_time
            )
        except Exception as e:
            return HealthStatus(
                component="telegram",
                status="degraded",
                message=f"Error verificando Telegram: {str(e)}",
                last_check=datetime.now()
            )
    
    def check_filesystem_health(self) -> HealthStatus:
        """Verifica el estado del sistema de archivos"""
        start_time = datetime.now()
        
        try:
            # Verificar directorios críticos
            critical_dirs = [
                Path("logs"),
                Path("models"),
                Path("data"),
            ]
            
            missing_dirs = []
            for dir_path in critical_dirs:
                if not dir_path.exists():
                    missing_dirs.append(str(dir_path))
            
            # Verificar espacio en disco
            import shutil
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024**3)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if missing_dirs:
                return HealthStatus(
                    component="filesystem",
                    status="degraded",
                    message=f"Directorios faltantes: {', '.join(missing_dirs)}",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details={"free_space_gb": free_gb}
                )
            elif free_gb < 1.0:  # Menos de 1GB libre
                return HealthStatus(
                    component="filesystem",
                    status="degraded",
                    message=f"Poco espacio en disco: {free_gb:.2f} GB libre",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details={"free_space_gb": free_gb}
                )
            else:
                return HealthStatus(
                    component="filesystem",
                    status="healthy",
                    message=f"Sistema de archivos OK. {free_gb:.2f} GB libre",
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    details={"free_space_gb": free_gb}
                )
        except Exception as e:
            return HealthStatus(
                component="filesystem",
                status="unhealthy",
                message=f"Error verificando sistema de archivos: {str(e)}",
                last_check=datetime.now()
            )
    
    def _generate_recommendations(self, components: List[HealthStatus]) -> List[str]:
        """Genera recomendaciones basadas en el estado de los componentes"""
        recommendations = []
        
        unhealthy = [c for c in components if c.status == 'unhealthy']
        degraded = [c for c in components if c.status == 'degraded']
        
        if unhealthy:
            recommendations.append(f"⚠️ {len(unhealthy)} componente(s) no saludable(s). Revisar inmediatamente.")
        
        if degraded:
            recommendations.append(f"⚡ {len(degraded)} componente(s) degradado(s). Monitorear de cerca.")
        
        # Recomendaciones específicas
        for component in components:
            if component.component == "trading_bot" and component.status == "unhealthy":
                recommendations.append("💡 El bot no está corriendo. Ejecutar: python run_bot.py --live --continuous")
            
            if component.component == "iol_connection" and component.status == "unhealthy":
                recommendations.append("💡 Verificar credenciales de IOL en .env")
            
            if component.component == "database" and component.status == "degraded":
                recommendations.append("💡 Considerar hacer backup de la base de datos")
            
            if component.component == "filesystem" and "Poco espacio" in component.message:
                recommendations.append("💡 Limpiar archivos antiguos o logs para liberar espacio")
        
        if not recommendations:
            recommendations.append("✅ Todos los componentes están saludables")
        
        return recommendations
    
    def get_health_summary(self) -> Dict:
        """Obtiene un resumen del estado de salud"""
        if not self._last_health_check:
            self.check_all()
        
        health = self._last_health_check
        
        return {
            "overall_status": health.overall_status,
            "timestamp": health.timestamp.isoformat(),
            "components": [asdict(c) for c in health.components],
            "metrics": health.metrics,
            "recommendations": health.recommendations
        }
    
    def get_health_history(self, hours: int = 24) -> List[Dict]:
        """Obtiene el historial de salud de las últimas N horas"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [h for h in self._health_history if h.timestamp >= cutoff]
        
        return [{
            "timestamp": h.timestamp.isoformat(),
            "overall_status": h.overall_status,
            "metrics": h.metrics
        } for h in recent]


# Función de conveniencia
def check_system_health() -> SystemHealth:
    """Función de conveniencia para verificar la salud del sistema"""
    monitor = HealthMonitor()
    return monitor.check_all()


if __name__ == "__main__":
    # Test del health monitor
    print("="*70)
    print("🏥 SISTEMA DE MONITOREO DE SALUD")
    print("="*70)
    print()
    
    monitor = HealthMonitor()
    health = monitor.check_all()
    
    print(f"Estado General: {health.overall_status.upper()}")
    print(f"Timestamp: {health.timestamp}")
    print()
    
    print("Componentes:")
    for component in health.components:
        status_icon = "✅" if component.status == "healthy" else "⚠️" if component.status == "degraded" else "❌"
        print(f"  {status_icon} {component.component}: {component.status}")
        print(f"     {component.message}")
        if component.response_time_ms:
            print(f"     Tiempo de respuesta: {component.response_time_ms:.2f} ms")
        print()
    
    print("Métricas:")
    for key, value in health.metrics.items():
        print(f"  {key}: {value}")
    print()
    
    print("Recomendaciones:")
    for rec in health.recommendations:
        print(f"  {rec}")

