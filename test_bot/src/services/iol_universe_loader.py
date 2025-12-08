"""
IOL Universe Loader - Carga TODOS los instrumentos disponibles en IOL
Permite analizar el universo completo de trading
"""
from typing import List, Dict
import requests


class IOLUniverseLoader:
    """Carga todos los instrumentos disponibles en IOL"""
    
    def __init__(self, iol_client):
        self.iol_client = iol_client
        
        # Categorías de instrumentos en IOL
        self.categories = {
            'acciones': 'acciones',  # Panel Líder + General
            'cedears': 'cedears',    # Acciones USA
            'bonos': 'titulos-publicos',  # Bonos soberanos
            'obligaciones': 'obligaciones-negociables',  # ONs
            'letras': 'letras',  # Letras del tesoro
            'fondos': 'fondos-comunes-de-inversion'
        }
    
    def get_all_instruments(self, categories: List[str] = None) -> Dict[str, List[str]]:
        """
        Obtiene todos los instrumentos de IOL
        
        Args:
            categories: Lista de categorías a incluir. Si None, incluye todas.
                       Opciones: 'acciones', 'cedears', 'bonos', 'obligaciones', 'letras', 'fondos'
        
        Returns:
            Dict con símbolos por categoría
        """
        if categories is None:
            categories = list(self.categories.keys())
        
        all_instruments = {}
        
        for category in categories:
            if category not in self.categories:
                continue
            
            try:
                symbols = self._get_category_symbols(category)
                all_instruments[category] = symbols
                print(f"✅ {category.upper()}: {len(symbols)} instrumentos")
            except Exception as e:
                print(f"⚠️  Error obteniendo {category}: {e}")
                all_instruments[category] = []
        
        return all_instruments
    
    def _get_category_symbols(self, category: str) -> List[str]:
        """Obtiene símbolos de una categoría específica"""
        
        if category == 'acciones':
            return self._get_acciones()
        elif category == 'cedears':
            return self._get_cedears()
        elif category == 'bonos':
            return self._get_bonos()
        elif category == 'obligaciones':
            return self._get_obligaciones()
        elif category == 'letras':
            return self._get_letras()
        elif category == 'fondos':
            return self._get_fondos()
        else:
            return []
    
    def _get_acciones(self) -> List[str]:
        """Obtiene todas las acciones argentinas"""
        try:
            # Usar API de IOL para obtener panel líder y general
            response = self.iol_client._make_request('GET', 'Titulos/Cotizacion/acciones/argentina/todos')
            
            if 'titulos' in response:
                symbols = [t['simbolo'] for t in response['titulos'] if t.get('simbolo')]
                return symbols
            
            # Fallback: Lista conocida de acciones principales
            return [
                'GGAL', 'YPFD', 'PAMP', 'BMA', 'ALUA', 'LOMA', 'TGNO4', 'TGSU2',
                'COME', 'EDN', 'TXAR', 'CRES', 'VALO', 'MIRG', 'BYMA', 'TRAN',
                'CVBA', 'BOLT', 'METR', 'CEPU', 'DGCU2', 'HAVA', 'IRSA', 'BHIP'
            ]
        except Exception as e:
            print(f"Error en acciones: {e}")
            return []
    
    def _get_cedears(self) -> List[str]:
        """Obtiene todos los CEDEARs"""
        try:
            response = self.iol_client._make_request('GET', 'Titulos/Cotizacion/cedears')
            
            if 'titulos' in response:
                symbols = [t['simbolo'] for t in response['titulos'] if t.get('simbolo')]
                return symbols
            
            # Fallback: CEDEARs más populares
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
                'DIS', 'KO', 'PEP', 'WMT', 'JPM', 'BAC', 'V', 'MA', 'PYPL',
                'TSM', 'INTC', 'AMD', 'QCOM', 'BA', 'CAT', 'GE', 'IBM',
                'ORCL', 'CRM', 'ADBE', 'CSCO', 'AVGO'
            ]
        except Exception as e:
            print(f"Error en cedears: {e}")
            return []
    
    def _get_bonos(self) -> List[str]:
        """Obtiene bonos soberanos"""
        try:
            response = self.iol_client._make_request('GET', 'Titulos/Cotizacion/titulosPublicos')
            
            if 'titulos' in response:
                symbols = [t['simbolo'] for t in response['titulos'] if t.get('simbolo')]
                return symbols
            
            # Fallback: Bonos más líquidos
            return [
                'GD30', 'GD35', 'GD38', 'GD41', 'GD46',
                'AL30', 'AL35', 'AL38', 'AL41', 'AE38'
            ]
        except Exception as e:
            print(f"Error en bonos: {e}")
            return []
    
    def _get_obligaciones(self) -> List[str]:
        """Obtiene obligaciones negociables"""
        try:
            # ONs más líquidas conocidas
            return [
                'PAMPY', 'PAMPO', 'TXARY', 'CRCCY', 'IRCP3',
                'YPF27', 'TGSU7', 'TGNO6'
            ]
        except Exception as e:
            print(f"Error en obligaciones: {e}")
            return []
    
    def _get_letras(self) -> List[str]:
        """Obtiene letras del tesoro"""
        try:
            # Letras comunes
            return ['S30E5', 'S31M5', 'S30J5', 'X26F5', 'X18D5']
        except Exception as e:
            return []
    
    def _get_fondos(self) -> List[str]:
        """Obtiene fondos comunes de inversión"""
        try:
            # FCIs más conocidos
            return []  # Por ahora vacío, los FCIs son diferentes
        except Exception as e:
            return []
    
    def get_tradeable_universe(self, max_symbols: int = 200) -> List[str]:
        """
        Obtiene universo completo de símbolos operables
        
        Args:
            max_symbols: Límite de símbolos (para evitar sobrecarga)
        
        Returns:
            Lista de símbolos únicos
        """
        print(f"\n{'='*70}")
        print("🌍 CARGANDO UNIVERSO COMPLETO DE IOL")
        print(f"{'='*70}")
        
        # Obtener todas las categorías
        all_instruments = self.get_all_instruments()
        
        # Combinar todos los símbolos
        all_symbols = []
        for category, symbols in all_instruments.items():
            all_symbols.extend(symbols)
        
        # Remover duplicados
        unique_symbols = list(set(all_symbols))
        
        # Limitar cantidad
        if len(unique_symbols) > max_symbols:
            print(f"\n⚠️  Limitando a {max_symbols} símbolos (de {len(unique_symbols)} totales)")
            # Priorizar: CEDEARs y acciones principales
            priority_symbols = []
            
            # 1. CEDEARs primero (más líquidos)
            cedears = all_instruments.get('cedears', [])
            priority_symbols.extend(cedears[:80])
            
            # 2. Acciones argentinas
            acciones = all_instruments.get('acciones', [])
            priority_symbols.extend(acciones[:60])
            
            # 3. Bonos más líquidos
            bonos = all_instruments.get('bonos', [])
            priority_symbols.extend(bonos[:30])
            
            # 4. Resto
            other = [s for s in unique_symbols if s not in priority_symbols]
            priority_symbols.extend(other[:30])
            
            unique_symbols = priority_symbols[:max_symbols]
        
        print(f"\n✅ UNIVERSO CARGADO: {len(unique_symbols)} símbolos")
        print(f"{'='*70}\n")
        
        return unique_symbols


# Test
if __name__ == "__main__":
    from src.connectors.iol_client import IOLClient
    
    print("Conectando a IOL...")
    iol = IOLClient()
    
    loader = IOLUniverseLoader(iol)
    universe = loader.get_tradeable_universe(max_symbols=100)
    
    print(f"\nPrimeros 20 símbolos:")
    print(', '.join(universe[:20]))




