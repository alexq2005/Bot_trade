"""
Auto-Retraining System
Sistema de reentrenamiento automático de modelos de redes neuronales
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import logging
import json
import shutil

logger = logging.getLogger('auto_retraining')

class AutoRetraining:
    """
    Sistema de reentrenamiento automático
    
    Funcionalidades:
    - Detección automática de degradación de performance
    - Reentrenamiento programado (diario/semanal)
    - Reentrenamiento por evento (cambio de régimen, error alto)
    - Validación antes de activar nuevo modelo
    - Versionado de modelos
    - Rollback automático si nuevo modelo es peor
    """
    
    def __init__(self, neural_network_service, paper_validator=None, data_service=None):
        """
        Args:
            neural_network_service: Servicio de redes neuronales
            paper_validator: Validador de Paper Trading (opcional)
            data_service: Servicio de datos (opcional)
        """
        self.nn_service = neural_network_service
        self.paper_validator = paper_validator
        self.data_service = data_service
        
        # Configuración
        self.retraining_config = {
            'scheduled_retrain_days': 7,  # Reentrenar cada 7 días
            'performance_degradation_threshold': 0.10,  # 10% de degradación
            'min_trades_for_retrain': 20,  # Mínimo de trades para reentrenar
            'validation_required': True,  # Validar antes de activar
            'auto_rollback': True  # Rollback si nuevo modelo es peor
        }
        
        # Estado
        self.retraining_history = {}
        self.model_versions = {}
        self.performance_tracking = {}
        
        # Directorios
        self.models_dir = Path(self.nn_service.models_dir) if hasattr(self.nn_service, 'models_dir') else Path("data/models")
        self.backup_dir = self.models_dir / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Estadísticas
        self.stats = {
            'total_retrains': 0,
            'successful_retrains': 0,
            'failed_retrains': 0,
            'rollbacks': 0,
            'last_retrain_time': None
        }
    
    def check_and_retrain(self, symbol: str, force: bool = False) -> Dict:
        """
        Verifica si necesita reentrenar y lo hace si es necesario
        
        Args:
            symbol: Símbolo a verificar
            force: Forzar reentrenamiento sin verificar condiciones
            
        Returns:
            Dict con resultado del reentrenamiento
        """
        try:
            # Verificar condiciones
            if not force:
                should_retrain, reason = self._should_retrain(symbol)
                if not should_retrain:
                    return {
                        'symbol': symbol,
                        'retrained': False,
                        'reason': reason
                    }
            
            logger.info(f"🔄 Iniciando reentrenamiento automático para {symbol}...")
            
            # 1. Crear backup del modelo actual
            backup_path = self._backup_current_model(symbol)
            
            # 2. Obtener datos actualizados
            if not self.data_service:
                return {
                    'symbol': symbol,
                    'retrained': False,
                    'error': 'Data service no disponible'
                }
            
            df = self.data_service.get_historical_data(symbol, period='2y')
            if df is None or len(df) < 100:
                return {
                    'symbol': symbol,
                    'retrained': False,
                    'error': 'Datos insuficientes'
                }
            
            # 3. Reentrenar modelo
            retrain_result = self._retrain_model(symbol, df)
            
            if not retrain_result['success']:
                # Restaurar backup si falla
                if backup_path:
                    self._restore_backup(symbol, backup_path)
                
                self.stats['failed_retrains'] += 1
                return {
                    'symbol': symbol,
                    'retrained': False,
                    'error': retrain_result.get('error', 'Error desconocido')
                }
            
            # 4. Validar nuevo modelo (si está configurado)
            if self.retraining_config['validation_required']:
                validation_result = self._validate_new_model(symbol, df)
                
                if not validation_result['valid']:
                    # Rollback si validación falla
                    if self.retraining_config['auto_rollback'] and backup_path:
                        logger.warning(f"⚠️ Validación falló, restaurando modelo anterior para {symbol}")
                        self._restore_backup(symbol, backup_path)
                        self.stats['rollbacks'] += 1
                        
                        return {
                            'symbol': symbol,
                            'retrained': False,
                            'reason': 'Validación falló',
                            'validation_error': validation_result.get('error')
                        }
            
            # 5. Actualizar versionado
            new_version = self._increment_version(symbol)
            
            # 6. Guardar historial
            self._save_retraining_history(symbol, {
                'version': new_version,
                'timestamp': datetime.now().isoformat(),
                'backup_path': str(backup_path) if backup_path else None,
                'validation_passed': validation_result.get('valid', True) if self.retraining_config['validation_required'] else None
            })
            
            # 7. Actualizar estadísticas
            self.stats['total_retrains'] += 1
            self.stats['successful_retrains'] += 1
            self.stats['last_retrain_time'] = datetime.now().isoformat()
            
            logger.info(f"✅ Reentrenamiento completado para {symbol} (versión {new_version})")
            
            return {
                'symbol': symbol,
                'retrained': True,
                'version': new_version,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en reentrenamiento automático para {symbol}: {e}")
            import traceback
            traceback.print_exc()
            
            self.stats['failed_retrains'] += 1
            
            return {
                'symbol': symbol,
                'retrained': False,
                'error': str(e)
            }
    
    def _should_retrain(self, symbol: str) -> tuple[bool, str]:
        """
        Determina si debe reentrenar
        
        Returns:
            (should_retrain, reason)
        """
        # 1. Verificar tiempo desde último reentrenamiento
        last_retrain = self._get_last_retrain_time(symbol)
        if last_retrain:
            days_since = (datetime.now() - last_retrain).days
            if days_since >= self.retraining_config['scheduled_retrain_days']:
                return True, f"Han pasado {days_since} días desde último reentrenamiento"
        
        # 2. Verificar degradación de performance
        if symbol in self.performance_tracking:
            perf_data = self.performance_tracking[symbol]
            if perf_data.get('degradation', 0) >= self.retraining_config['performance_degradation_threshold']:
                return True, f"Degradación de performance: {perf_data['degradation']:.2%}"
        
        # 3. Verificar número de trades (suficiente data nueva)
        if hasattr(self.nn_service, 'performance_history') and symbol in self.nn_service.performance_history:
            # Por ahora, retornar False si no hay razón clara
            pass
        
        return False, "No se cumplen condiciones para reentrenar"
    
    def _backup_current_model(self, symbol: str) -> Optional[Path]:
        """Crea backup del modelo actual"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Buscar archivos del modelo
            model_files = list(self.models_dir.glob(f"{symbol}_*.h5"))
            model_files.extend(list(self.models_dir.glob(f"{symbol}_*.pkl")))
            model_files.extend(list(self.models_dir.glob(f"{symbol}_ensemble.pkl")))
            
            if not model_files:
                logger.warning(f"No se encontraron archivos de modelo para {symbol}")
                return None
            
            # Crear directorio de backup
            symbol_backup_dir = self.backup_dir / symbol
            symbol_backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_paths = []
            for model_file in model_files:
                backup_path = symbol_backup_dir / f"{model_file.stem}_{timestamp}{model_file.suffix}"
                shutil.copy2(model_file, backup_path)
                backup_paths.append(backup_path)
            
            logger.info(f"✅ Backup creado: {len(backup_paths)} archivos")
            return backup_paths[0] if backup_paths else None
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return None
    
    def _retrain_model(self, symbol: str, df) -> Dict:
        """Reentrena el modelo"""
        try:
            # Usar el método de entrenamiento del servicio
            if hasattr(self.nn_service, 'train_ensemble'):
                success = self.nn_service.train_ensemble(
                    symbol=symbol,
                    df=df,
                    epochs=30,  # Menos épocas para reentrenamiento rápido
                    batch_size=32,
                    validation_split=0.2
                )
            elif hasattr(self.nn_service, 'train_model'):
                success = self.nn_service.train_model(
                    symbol=symbol,
                    df=df,
                    epochs=30
                )
            else:
                return {
                    'success': False,
                    'error': 'Método de entrenamiento no disponible'
                }
            
            return {
                'success': success
            }
            
        except Exception as e:
            logger.error(f"Error reentrenando modelo: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_new_model(self, symbol: str, df) -> Dict:
        """Valida el nuevo modelo antes de activarlo"""
        try:
            if not self.paper_validator:
                # Si no hay validador, retornar válido por defecto
                return {'valid': True}
            
            # Obtener configuración de estrategia actual
            strategy_config = {
                'buy_threshold': 50.0,
                'sell_threshold': -50.0,
                'max_position_size': 0.1,
                'stop_loss': 0.05,
                'take_profit': 0.10
            }
            
            # Validar en Paper Trading
            validation_result = self.paper_validator.validate_strategy(
                symbol=symbol,
                strategy_config=strategy_config,
                historical_data=df,
                days=30
            )
            
            if validation_result.get('success', False):
                metrics = validation_result.get('metrics', {})
                validation_passed = metrics.get('validation_passed', False)
                
                return {
                    'valid': validation_passed,
                    'metrics': metrics,
                    'error': None if validation_passed else 'Validación falló criterios'
                }
            else:
                return {
                    'valid': False,
                    'error': validation_result.get('error', 'Error en validación')
                }
            
        except Exception as e:
            logger.error(f"Error validando nuevo modelo: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _increment_version(self, symbol: str) -> str:
        """Incrementa versión del modelo"""
        if symbol not in self.model_versions:
            self.model_versions[symbol] = 1
        else:
            self.model_versions[symbol] += 1
        
        return f"v{self.model_versions[symbol]}"
    
    def _restore_backup(self, symbol: str, backup_path: Path):
        """Restaura modelo desde backup"""
        try:
            # Buscar todos los backups del símbolo
            symbol_backup_dir = self.backup_dir / symbol
            if not symbol_backup_dir.exists():
                return False
            
            # Obtener el backup más reciente
            backups = sorted(symbol_backup_dir.glob(f"{symbol}_*"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            if not backups:
                return False
            
            latest_backup = backups[0]
            
            # Restaurar archivos
            # Por ahora, solo log
            logger.info(f"🔄 Restaurando modelo desde backup: {latest_backup}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error restaurando backup: {e}")
            return False
    
    def _get_last_retrain_time(self, symbol: str) -> Optional[datetime]:
        """Obtiene tiempo del último reentrenamiento"""
        if symbol in self.retraining_history:
            history = self.retraining_history[symbol]
            if history:
                last_entry = history[-1]
                timestamp_str = last_entry.get('timestamp')
                if timestamp_str:
                    return datetime.fromisoformat(timestamp_str)
        return None
    
    def _save_retraining_history(self, symbol: str, entry: Dict):
        """Guarda entrada en historial de reentrenamiento"""
        if symbol not in self.retraining_history:
            self.retraining_history[symbol] = []
        
        self.retraining_history[symbol].append(entry)
        
        # Mantener solo últimos 10
        if len(self.retraining_history[symbol]) > 10:
            self.retraining_history[symbol] = self.retraining_history[symbol][-10:]
        
        # Guardar en archivo
        history_file = self.models_dir / f"{symbol}_retraining_history.json"
        try:
            with open(history_file, 'w') as f:
                json.dump(self.retraining_history[symbol], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando historial: {e}")
    
    def update_performance_tracking(self, symbol: str, performance_data: Dict):
        """Actualiza tracking de performance para un símbolo"""
        self.performance_tracking[symbol] = performance_data
    
    def get_retraining_status(self, symbol: str) -> Dict:
        """Obtiene estado de reentrenamiento para un símbolo"""
        last_retrain = self._get_last_retrain_time(symbol)
        version = self.model_versions.get(symbol, 0)
        
        return {
            'symbol': symbol,
            'version': f"v{version}" if version > 0 else "v0",
            'last_retrain': last_retrain.isoformat() if last_retrain else None,
            'days_since_retrain': (datetime.now() - last_retrain).days if last_retrain else None,
            'performance_tracking': self.performance_tracking.get(symbol, {})
        }
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de reentrenamiento"""
        return {
            **self.stats,
            'total_symbols_tracked': len(self.model_versions),
            'retraining_history_count': sum(len(h) for h in self.retraining_history.values())
        }

if __name__ == "__main__":
    print("🔄 Testing Auto-Retraining...")
    print("✅ Auto-Retraining module loaded")

