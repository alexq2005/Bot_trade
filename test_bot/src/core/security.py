"""
Sistema de Seguridad y Gestión de Secretos
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict
from cryptography.fernet import Fernet
import base64

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from src.core.logger import get_logger

logger = get_logger("security")


class SecretManager:
    """
    Gestor de secretos seguro usando keyring y encriptación
    """
    
    def __init__(self, service_name: str = "iol_quantum_ai"):
        """
        Args:
            service_name: Nombre del servicio para keyring
        """
        self.service_name = service_name
        self.keyring_available = KEYRING_AVAILABLE
        self._encryption_key = None
        self._cipher = None
    
    def _get_encryption_key(self) -> bytes:
        """Obtiene o genera la clave de encriptación"""
        if self._encryption_key is None:
            # Intentar obtener de variable de entorno
            key_env = os.getenv("ENCRYPTION_KEY")
            if key_env:
                self._encryption_key = key_env.encode()
            else:
                # Generar clave desde una semilla (no ideal para producción, pero funcional)
                seed = os.getenv("ENCRYPTION_SEED", "default_seed_change_in_production")
                key = base64.urlsafe_b64encode(seed.encode()[:32].ljust(32, b'0'))
                self._encryption_key = key
            
            self._cipher = Fernet(self._encryption_key)
        
        return self._encryption_key
    
    def store_secret(self, key: str, value: str, use_keyring: bool = True) -> bool:
        """
        Almacena un secreto de forma segura
        
        Args:
            key: Nombre del secreto
            value: Valor a almacenar
            use_keyring: Si usar keyring (recomendado) o archivo encriptado
        
        Returns:
            True si se almacenó correctamente
        """
        try:
            if use_keyring and self.keyring_available:
                keyring.set_password(self.service_name, key, value)
                logger.info(f"Secreto '{key}' almacenado en keyring")
                return True
            else:
                # Fallback: almacenar en archivo encriptado
                self._store_encrypted(key, value)
                return True
        except Exception as e:
            logger.error(f"Error almacenando secreto '{key}': {e}")
            return False
    
    def get_secret(self, key: str, use_keyring: bool = True) -> Optional[str]:
        """
        Obtiene un secreto almacenado
        
        Args:
            key: Nombre del secreto
            use_keyring: Si buscar en keyring primero
        
        Returns:
            Valor del secreto o None si no existe
        """
        try:
            if use_keyring and self.keyring_available:
                value = keyring.get_password(self.service_name, key)
                if value:
                    return value
            
            # Fallback: leer de archivo encriptado
            return self._get_encrypted(key)
        except Exception as e:
            logger.error(f"Error obteniendo secreto '{key}': {e}")
            return None
    
    def delete_secret(self, key: str) -> bool:
        """Elimina un secreto"""
        try:
            if self.keyring_available:
                try:
                    keyring.delete_password(self.service_name, key)
                except keyring.errors.PasswordDeleteError:
                    pass  # No existe, está bien
            
            # Eliminar de archivo encriptado también
            self._delete_encrypted(key)
            return True
        except Exception as e:
            logger.error(f"Error eliminando secreto '{key}': {e}")
            return False
    
    def _store_encrypted(self, key: str, value: str):
        """Almacena en archivo encriptado"""
        secrets_file = Path(".secrets.encrypted")
        
        # Leer secretos existentes
        secrets = {}
        if secrets_file.exists():
            try:
                with open(secrets_file, 'rb') as f:
                    encrypted_data = f.read()
                    decrypted = self._cipher.decrypt(encrypted_data)
                    secrets = json.loads(decrypted.decode())
            except Exception:
                secrets = {}
        
        # Agregar nuevo secreto
        secrets[key] = value
        
        # Guardar encriptado
        data = json.dumps(secrets).encode()
        encrypted = self._cipher.encrypt(data)
        
        with open(secrets_file, 'wb') as f:
            f.write(encrypted)
        
        # Asegurar permisos restrictivos (solo owner puede leer)
        secrets_file.chmod(0o600)
    
    def _get_encrypted(self, key: str) -> Optional[str]:
        """Lee de archivo encriptado"""
        secrets_file = Path(".secrets.encrypted")
        
        if not secrets_file.exists():
            return None
        
        try:
            with open(secrets_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted = self._cipher.decrypt(encrypted_data)
                secrets = json.loads(decrypted.decode())
                return secrets.get(key)
        except Exception as e:
            logger.error(f"Error leyendo secreto encriptado '{key}': {e}")
            return None
    
    def _delete_encrypted(self, key: str):
        """Elimina de archivo encriptado"""
        secrets_file = Path(".secrets.encrypted")
        
        if not secrets_file.exists():
            return
        
        try:
            with open(secrets_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted = self._cipher.decrypt(encrypted_data)
                secrets = json.loads(decrypted.decode())
            
            if key in secrets:
                del secrets[key]
                
                # Guardar actualizado
                data = json.dumps(secrets).encode()
                encrypted = self._cipher.encrypt(data)
                
                with open(secrets_file, 'wb') as f:
                    f.write(encrypted)
        except Exception as e:
            logger.error(f"Error eliminando secreto encriptado '{key}': {e}")


class OrderValidator:
    """
    Validador de órdenes antes de ejecutar
    """
    
    def __init__(self, max_order_size: float = 100000.0, max_order_percent: float = 10.0):
        """
        Args:
            max_order_size: Tamaño máximo de orden en pesos
            max_order_percent: Porcentaje máximo del capital por orden
        """
        self.max_order_size = max_order_size
        self.max_order_percent = max_order_percent
    
    def validate_order(self, symbol: str, quantity: int, price: float, 
                      current_capital: float, side: str = 'buy') -> tuple[bool, Optional[str]]:
        """
        Valida una orden antes de ejecutar
        
        Args:
            symbol: Símbolo a operar
            quantity: Cantidad
            price: Precio
            current_capital: Capital actual
            side: 'buy' o 'sell'
        
        Returns:
            (is_valid, error_message)
        """
        # Validar símbolo
        if not symbol or len(symbol) == 0:
            return False, "Símbolo inválido"
        
        # Validar cantidad
        if quantity <= 0:
            return False, "Cantidad debe ser mayor a 0"
        
        if quantity > 1000000:  # Límite razonable
            return False, "Cantidad excede el límite máximo"
        
        # Validar precio
        if price <= 0:
            return False, "Precio debe ser mayor a 0"
        
        # Calcular valor de la orden
        order_value = quantity * price
        
        # Validar tamaño de orden
        if order_value > self.max_order_size:
            return False, f"Valor de orden (${order_value:,.2f}) excede el máximo permitido (${self.max_order_size:,.2f})"
        
        # Validar porcentaje del capital
        if side == 'buy':
            order_percent = (order_value / current_capital) * 100
            if order_percent > self.max_order_percent:
                return False, f"Orden representa {order_percent:.2f}% del capital, máximo permitido: {self.max_order_percent}%"
        
        # Validar que haya suficiente capital (solo para compras)
        if side == 'buy' and order_value > current_capital:
            return False, f"Capital insuficiente. Necesitas ${order_value:,.2f}, tienes ${current_capital:,.2f}"
        
        return True, None
    
    def requires_confirmation(self, order_value: float, current_capital: float) -> bool:
        """
        Determina si una orden requiere confirmación manual
        
        Args:
            order_value: Valor de la orden
            current_capital: Capital actual
        
        Returns:
            True si requiere confirmación
        """
        # Requerir confirmación si:
        # - Orden > 5% del capital
        # - Orden > $10,000
        order_percent = (order_value / current_capital) * 100
        return order_percent > 5.0 or order_value > 10000.0


class AuditLogger:
    """
    Logger de auditoría para operaciones críticas
    """
    
    def __init__(self, audit_file: str = "audit.log"):
        """
        Args:
            audit_file: Archivo donde guardar los logs de auditoría
        """
        self.audit_file = Path(audit_file)
        self.logger = get_logger("audit")
    
    def log_operation(self, operation_type: str, details: Dict, user: Optional[str] = None):
        """
        Registra una operación crítica
        
        Args:
            operation_type: Tipo de operación (ORDER_EXECUTED, CONFIG_CHANGED, etc.)
            details: Detalles de la operación
            user: Usuario que ejecutó la operación (opcional)
        """
        from datetime import datetime
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation_type,
            "user": user or "system",
            "details": details
        }
        
        # Log a archivo
        try:
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            self.logger.error(f"Error escribiendo log de auditoría: {e}")
        
        # También log normal
        self.logger.info(f"AUDIT: {operation_type} - {json.dumps(details)}")
    
    def get_audit_history(self, hours: int = 24) -> list:
        """Obtiene el historial de auditoría de las últimas N horas"""
        from datetime import datetime, timedelta
        
        if not self.audit_file.exists():
            return []
        
        cutoff = datetime.now() - timedelta(hours=hours)
        history = []
        
        try:
            with open(self.audit_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time >= cutoff:
                            history.append(entry)
        except Exception as e:
            self.logger.error(f"Error leyendo historial de auditoría: {e}")
        
        return history


# Instancias globales
_secret_manager = None
_order_validator = None
_audit_logger = None


def get_secret_manager() -> SecretManager:
    """Obtiene la instancia global de SecretManager"""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager


def get_order_validator() -> OrderValidator:
    """Obtiene la instancia global de OrderValidator"""
    global _order_validator
    if _order_validator is None:
        _order_validator = OrderValidator()
    return _order_validator


def get_audit_logger() -> AuditLogger:
    """Obtiene la instancia global de AuditLogger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

