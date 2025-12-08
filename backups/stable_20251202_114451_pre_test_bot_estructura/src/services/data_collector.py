"""
Data Collector Service
Recopila datos históricos de mercado desde IOL para símbolos que no tienen datos.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import pandas as pd

from src.core.database import SessionLocal
from src.models.market_data import MarketData
from src.connectors.iol_client import IOLClient
from src.connectors.byma_client import BYMAClient
from src.connectors.multi_source_client import MultiSourceDataClient
from src.core.logger import get_logger

logger = get_logger("data_collector")


class DataCollector:
    """
    Servicio para recopilar datos históricos de mercado desde IOL.
    """
    
    def __init__(self, iol_client: Optional[IOLClient] = None):
        """
        Args:
            iol_client: Cliente IOL (se crea uno nuevo si es None)
        """
        self.iol_client = iol_client or IOLClient()
        self.byma_client = BYMAClient()
        self.multi_source = MultiSourceDataClient()  # Cliente multi-fuente
    
    def check_symbol_has_data(self, symbol: str, min_records: int = 100) -> bool:
        """
        Verifica si un símbolo tiene suficientes datos históricos.
        
        Args:
            symbol: Símbolo a verificar
            min_records: Número mínimo de registros requeridos
        
        Returns:
            True si tiene suficientes datos, False en caso contrario
        """
        db = SessionLocal()
        try:
            count = db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).count()
            return count >= min_records
        finally:
            db.close()
    
    def get_symbols_without_data(self, symbols: List[str], min_records: int = 100) -> List[str]:
        """
        Obtiene la lista de símbolos que no tienen suficientes datos.
        
        Args:
            symbols: Lista de símbolos a verificar
            min_records: Número mínimo de registros requeridos
        
        Returns:
            Lista de símbolos sin datos suficientes
        """
        symbols_without_data = []
        for symbol in symbols:
            if not self.check_symbol_has_data(symbol, min_records):
                symbols_without_data.append(symbol)
        return symbols_without_data
    
    def collect_historical_data(self, symbol: str, days: int = 365, market: Optional[str] = None, 
                               use_byma: bool = True) -> Dict:
        """
        Recopila datos históricos para un símbolo desde múltiples fuentes.
        
        Prioridad:
        1. BYMA/Yahoo Finance (datos históricos completos)
        2. IOL API (solo datos actuales)
        
        Args:
            symbol: Símbolo a recopilar
            days: Días de datos a recopilar
            market: Mercado del símbolo (auto-detectado si es None)
            use_byma: Si True, intenta obtener datos históricos desde BYMA/Yahoo
        
        Returns:
            Dict con resultado: {'success': bool, 'records_added': int, 'message': str}
        """
        db = SessionLocal()
        records_added = 0
        
        try:
            # Método 1: Intentar obtener datos históricos desde múltiples fuentes
            if use_byma:
                logger.info(f"Intentando obtener datos históricos desde múltiples fuentes para {symbol}...")
                
                # Calcular período basado en días
                if days >= 365:
                    period = "1y"
                elif days >= 180:
                    period = "6mo"
                elif days >= 90:
                    period = "3mo"
                elif days >= 30:
                    period = "1mo"
                else:
                    period = "5d"
                
                # Usar cliente multi-fuente (intenta Yahoo, BYMA, Alpha Vantage, etc.)
                result = self.multi_source.get_history(symbol, period=period, interval="1d")
                history = result.get('data', pd.DataFrame())
                source_name = result.get('source', 'Unknown')
                
                if history.empty:
                    # Fallback a BYMA directo
                    history = self.byma_client.get_history(symbol, period=period, interval="1d", 
                                                          iol_client=self.iol_client)
                    source_name = "BYMA/Yahoo"
                
                if not history.empty:
                    logger.info(f"✅ Obtenidos {len(history)} registros históricos desde {source_name} para {symbol}")
                    
                    # Guardar todos los registros en la base de datos
                    for index, row in history.iterrows():
                        # Verificar si ya existe
                        existing = db.query(MarketData).filter(
                            MarketData.symbol == symbol,
                            MarketData.timestamp == index
                        ).first()
                        
                        if existing:
                            # Actualizar
                            existing.open = row.get('Open', row.get('open', 0))
                            existing.high = row.get('High', row.get('high', 0))
                            existing.low = row.get('Low', row.get('low', 0))
                            existing.close = row.get('Close', row.get('close', 0))
                            existing.volume = row.get('Volume', row.get('volume', 0))
                            existing.source = source_name.lower().replace(' ', '_')
                        else:
                            # Crear nuevo
                            new_record = MarketData(
                                symbol=symbol,
                                timestamp=index,
                                open=row.get('Open', row.get('open', 0)),
                                high=row.get('High', row.get('high', 0)),
                                low=row.get('Low', row.get('low', 0)),
                                close=row.get('Close', row.get('close', 0)),
                                volume=row.get('Volume', row.get('volume', 0)),
                                source=source_name.lower().replace(' ', '_')
                            )
                            db.add(new_record)
                            records_added += 1
                    
                    db.commit()
                    
                    return {
                        'success': True,
                        'records_added': records_added,
                        'message': f"Datos históricos recopilados exitosamente para {symbol} ({records_added} nuevos registros)"
                    }
                else:
                    logger.warning(f"No se pudieron obtener datos históricos desde BYMA/Yahoo para {symbol}")
            
            # Método 2: Fallback a IOL (solo datos actuales)
            logger.info(f"Obteniendo cotización actual desde IOL para {symbol}...")
            quote = self.iol_client.get_quote(symbol, market)
            
            if 'error' in quote:
                return {
                    'success': False,
                    'records_added': 0,
                    'message': f"Error obteniendo cotización: {quote.get('error', 'Error desconocido')}"
                }
            
            # Extraer datos de la cotización
            # Nota: IOL API puede no proporcionar datos históricos completos
            # Este método guarda la cotización actual como un punto de datos
            
            price = quote.get('ultimoPrecio') or quote.get('precio') or quote.get('price')
            if not price:
                return {
                    'success': False,
                    'records_added': 0,
                    'message': "No se pudo obtener precio de la cotización"
                }
            
            # Verificar si ya existe un registro para hoy
            today = datetime.now().date()
            existing = db.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.timestamp >= datetime.combine(today, datetime.min.time())
            ).first()
            
            if existing:
                # Actualizar registro existente
                existing.close = price
                existing.volume = quote.get('volumen', 0) or quote.get('volume', 0)
                existing.high = quote.get('maximo', price) or quote.get('high', price)
                existing.low = quote.get('minimo', price) or quote.get('low', price)
                existing.open = quote.get('apertura', price) or quote.get('open', price)
                existing.source = "iol"
                records_added = 0  # No se agregó, solo se actualizó
            else:
                # Crear nuevo registro
                new_record = MarketData(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    close=price,
                    volume=quote.get('volumen', 0) or quote.get('volume', 0),
                    high=quote.get('maximo', price) or quote.get('high', price),
                    low=quote.get('minimo', price) or quote.get('low', price),
                    open=quote.get('apertura', price) or quote.get('open', price),
                    source="iol"
                )
                db.add(new_record)
                records_added = 1
            
            db.commit()
            
            return {
                'success': True,
                'records_added': records_added,
                'message': f"Datos recopilados exitosamente para {symbol}"
            }
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error recopilando datos para {symbol}: {e}")
            return {
                'success': False,
                'records_added': 0,
                'message': f"Error: {str(e)}"
            }
        finally:
            db.close()
    
    def collect_data_for_symbols(self, symbols: List[str], delay: float = 1.0) -> Dict[str, Dict]:
        """
        Recopila datos para múltiples símbolos.
        
        Args:
            symbols: Lista de símbolos
            delay: Delay entre requests (segundos)
        
        Returns:
            Dict con resultados por símbolo
        """
        results = {}
        
        for symbol in symbols:
            logger.info(f"Recopilando datos para {symbol}...")
            result = self.collect_historical_data(symbol)
            results[symbol] = result
            
            # Delay para no sobrecargar la API
            if delay > 0:
                time.sleep(delay)
        
        return results
    
    def get_data_status(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Obtiene el estado de datos para una lista de símbolos.
        
        Args:
            symbols: Lista de símbolos
        
        Returns:
            Dict con estado por símbolo: {symbol: {'has_data': bool, 'record_count': int}}
        """
        db = SessionLocal()
        status = {}
        
        try:
            for symbol in symbols:
                count = db.query(MarketData).filter(
                    MarketData.symbol == symbol
                ).count()
                
                status[symbol] = {
                    'has_data': count >= 100,
                    'record_count': count
                }
        finally:
            db.close()
        
        return status

