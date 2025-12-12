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
    
    def get_panel_general_symbols(self, max_symbols: int = 500) -> List[str]:
        """
        Obtiene TODOS los símbolos del Panel General de IOL.
        Este es el método más completo y confiable.
        
        Args:
            max_symbols: Límite máximo de símbolos a retornar
        
        Returns:
            Lista de símbolos únicos
        """
        try:
            print("   🔄 Obteniendo Panel General completo de IOL...")
            panel_data = self.iol_client.get_panel_general()
            
            if 'error' in panel_data:
                print(f"   ⚠️  Error en Panel General: {panel_data.get('error')}")
                return []
            
            symbols = []
            
            # Intentar diferentes estructuras de respuesta
            if isinstance(panel_data, dict):
                # Estructura 1: {'titulos': [...]}
                if 'titulos' in panel_data:
                    for titulo in panel_data['titulos']:
                        if isinstance(titulo, dict) and titulo.get('simbolo'):
                            symbols.append(titulo['simbolo'])
                # Estructura 2: {'data': {'titulos': [...]}}
                elif 'data' in panel_data and isinstance(panel_data['data'], dict):
                    if 'titulos' in panel_data['data']:
                        for titulo in panel_data['data']['titulos']:
                            if isinstance(titulo, dict) and titulo.get('simbolo'):
                                symbols.append(titulo['simbolo'])
                # Estructura 3: Claves directas con listas
                else:
                    for key, value in panel_data.items():
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) and item.get('simbolo'):
                                    symbols.append(item['simbolo'])
            elif isinstance(panel_data, list):
                # Si es una lista directa
                for item in panel_data:
                    if isinstance(item, dict) and item.get('simbolo'):
                        symbols.append(item['simbolo'])
            
            # Remover duplicados y limpiar
            unique_symbols = list(set([s.strip().upper() for s in symbols if s and s.strip()]))
            
            # Limitar cantidad
            if len(unique_symbols) > max_symbols:
                unique_symbols = unique_symbols[:max_symbols]
            
            if unique_symbols:
                print(f"   ✅ Panel General: {len(unique_symbols)} símbolos obtenidos")
                return unique_symbols
            else:
                print("   ⚠️  Panel General retornó lista vacía")
                return []
                
        except Exception as e:
            print(f"   ⚠️  Error obteniendo Panel General: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_acciones(self) -> List[str]:
        """Obtiene todas las acciones argentinas"""
        try:
            # PRIMERO: Intentar Panel General (más completo)
            panel_symbols = self.get_panel_general_symbols(max_symbols=200)
            if panel_symbols:
                # Filtrar solo acciones argentinas (excluir CEDEARs que suelen tener sufijos)
                acciones = [s for s in panel_symbols if not any(x in s.upper() for x in ['D', 'C', '.BA'])]
                if acciones:
                    return acciones[:100]  # Limitar a 100 acciones principales
            
            # FALLBACK: Usar API específica de acciones
            response = self.iol_client._make_request('GET', 'Titulos/Cotizacion/acciones/argentina/todos')
            
            if response and isinstance(response, dict):
                # Intentar diferentes estructuras de respuesta
                if 'titulos' in response:
                    symbols = [t['simbolo'] for t in response['titulos'] if t.get('simbolo')]
                    if symbols:
                        return symbols
                elif isinstance(response, list):
                    symbols = [t['simbolo'] for t in response if isinstance(t, dict) and t.get('simbolo')]
                    if symbols:
                        return symbols
            
            # Fallback final: Lista conocida de acciones principales
            print("   ⚠️  Usando lista de fallback para acciones")
            return [
                'GGAL', 'YPFD', 'PAMP', 'BMA', 'ALUA', 'LOMA', 'TGNO4', 'TGSU2',
                'COME', 'EDN', 'TXAR', 'CRES', 'VALO', 'MIRG', 'BYMA', 'TRAN',
                'CVBA', 'BOLT', 'METR', 'CEPU', 'DGCU2', 'HAVA', 'IRSA', 'BHIP'
            ]
        except Exception as e:
            print(f"   ⚠️  Error obteniendo acciones desde IOL: {e}")
            # Retornar fallback en caso de error
            return [
                'GGAL', 'YPFD', 'PAMP', 'BMA', 'ALUA', 'LOMA', 'TGNO4', 'TGSU2',
                'COME', 'EDN', 'TXAR', 'CRES', 'VALO', 'MIRG', 'BYMA', 'TRAN',
                'CVBA', 'BOLT', 'METR', 'CEPU', 'DGCU2', 'HAVA', 'IRSA', 'BHIP'
            ]
    
    def _get_cedears(self) -> List[str]:
        """Obtiene todos los CEDEARs"""
        try:
            response = self.iol_client._make_request('GET', 'Titulos/Cotizacion/cedears')
            
            if response and isinstance(response, dict):
                if 'titulos' in response:
                    symbols = [t['simbolo'] for t in response['titulos'] if t.get('simbolo')]
                    if symbols:
                        return symbols
                elif isinstance(response, list):
                    symbols = [t['simbolo'] for t in response if isinstance(t, dict) and t.get('simbolo')]
                    if symbols:
                        return symbols
            
            # Fallback: CEDEARs más populares
            print("   ⚠️  Usando lista de fallback para CEDEARs")
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
                'DIS', 'KO', 'PEP', 'WMT', 'JPM', 'BAC', 'V', 'MA', 'PYPL',
                'TSM', 'INTC', 'AMD', 'QCOM', 'BA', 'CAT', 'GE', 'IBM',
                'ORCL', 'CRM', 'ADBE', 'CSCO', 'AVGO'
            ]
        except Exception as e:
            print(f"   ⚠️  Error obteniendo CEDEARs desde IOL: {e}")
            # Retornar fallback en caso de error
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
                'DIS', 'KO', 'PEP', 'WMT', 'JPM', 'BAC', 'V', 'MA', 'PYPL',
                'TSM', 'INTC', 'AMD', 'QCOM', 'BA', 'CAT', 'GE', 'IBM',
                'ORCL', 'CRM', 'ADBE', 'CSCO', 'AVGO'
            ]
    
    def _get_bonos(self) -> List[str]:
        """Obtiene bonos soberanos"""
        try:
            response = self.iol_client._make_request('GET', 'Titulos/Cotizacion/titulosPublicos')
            
            if response and isinstance(response, dict):
                if 'titulos' in response:
                    symbols = [t['simbolo'] for t in response['titulos'] if t.get('simbolo')]
                    if symbols:
                        return symbols
                elif isinstance(response, list):
                    symbols = [t['simbolo'] for t in response if isinstance(t, dict) and t.get('simbolo')]
                    if symbols:
                        return symbols
            
            # Fallback: Bonos más líquidos
            print("   ⚠️  Usando lista de fallback para bonos")
            return [
                'GD30', 'GD35', 'GD38', 'GD41', 'GD46',
                'AL30', 'AL35', 'AL38', 'AL41', 'AE38'
            ]
        except Exception as e:
            print(f"   ⚠️  Error obteniendo bonos desde IOL: {e}")
            # Retornar fallback en caso de error
            return [
                'GD30', 'GD35', 'GD38', 'GD41', 'GD46',
                'AL30', 'AL35', 'AL38', 'AL41', 'AE38'
            ]
    
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
    
    def get_tradeable_universe(self, max_symbols: int = 200, categories: List[str] = None) -> List[str]:
        """
        Obtiene universo completo de símbolos operables.
        PRIORIZA Panel General de IOL (más completo y confiable).
        
        Args:
            max_symbols: Límite de símbolos (para evitar sobrecarga)
            categories: Lista de categorías a incluir (acciones, cedears, bonos, etc.)
        
        Returns:
            Lista de símbolos únicos
        """
        print(f"\n{'='*70}")
        print("🌍 CARGANDO UNIVERSO COMPLETO DE IOL")
        print(f"{'='*70}")
        
        # ESTRATEGIA 1: Panel General (MÁS COMPLETO Y RECOMENDADO)
        try:
            print("   🔄 Estrategia Principal: Panel General de IOL...")
            panel_symbols = self.get_panel_general_symbols(max_symbols=max_symbols)
            if panel_symbols and len(panel_symbols) > 0:
                print(f"\n✅ UNIVERSO CARGADO DESDE PANEL GENERAL: {len(panel_symbols)} símbolos")
                print(f"{'='*70}\n")
                return panel_symbols
            else:
                print("   ⚠️  Panel General no retornó símbolos, usando estrategia alternativa...")
        except Exception as e:
            print(f"   ⚠️  Error con Panel General: {e}")
        
        # ESTRATEGIA 2: Cargar por categorías (fallback)
        print("   🔄 Estrategia Alternativa: Cargando por categorías...")
        # Usar categories si se proporcionó, sino usar todas las categorías por defecto
        categories_to_use = categories if categories else ['acciones', 'cedears', 'bonos']
        all_instruments = self.get_all_instruments(categories=categories_to_use)
        
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



