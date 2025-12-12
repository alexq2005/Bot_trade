"""
Web Search Agent - Acceso a información de internet
Permite al bot buscar información en tiempo real
"""
import requests
from typing import Dict, List, Optional
from datetime import datetime
import json


class WebSearchAgent:
    """
    Agente que permite buscar información en internet
    """
    
    def __init__(self):
        # Puedes usar diferentes APIs de búsqueda
        # Opción 1: DuckDuckGo (gratis, sin API key)
        # Opción 2: Google Custom Search (requiere API key)
        # Opción 3: SerpAPI (requiere API key)
        
        self.search_engine = 'duckduckgo'  # Default
        self.api_key = None
        
    def search(self, query: str, num_results: int = 5) -> Dict:
        """
        Busca información en internet
        
        Args:
            query: Término de búsqueda
            num_results: Número de resultados deseados
            
        Returns:
            Dict con resultados de búsqueda
        """
        try:
            if self.search_engine == 'duckduckgo':
                return self._search_duckduckgo(query, num_results)
            elif self.search_engine == 'google':
                return self._search_google(query, num_results)
            else:
                return {'error': 'Motor de búsqueda no configurado'}
        except Exception as e:
            return {'error': f'Error en búsqueda: {str(e)}'}
    
    def _search_duckduckgo(self, query: str, num_results: int) -> Dict:
        """
        Búsqueda usando DuckDuckGo (gratis, sin API key)
        """
        try:
            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            
            # Extraer respuesta directa si existe
            if data.get('AbstractText'):
                results.append({
                    'title': data.get('Heading', 'Resultado'),
                    'snippet': data.get('AbstractText', ''),
                    'url': data.get('AbstractURL', ''),
                    'source': 'DuckDuckGo Instant Answer'
                })
            
            # Extraer enlaces relacionados
            if data.get('RelatedTopics'):
                for topic in data.get('RelatedTopics', [])[:num_results-1]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append({
                            'title': topic.get('Text', '')[:100],
                            'snippet': topic.get('Text', ''),
                            'url': topic.get('FirstURL', ''),
                            'source': 'DuckDuckGo Related'
                        })
            
            # Si no hay resultados, intentar búsqueda web
            if not results:
                return self._search_duckduckgo_web(query, num_results)
            
            return {
                'query': query,
                'results': results[:num_results],
                'timestamp': datetime.now().isoformat(),
                'engine': 'duckduckgo'
            }
            
        except Exception as e:
            return {'error': f'Error en búsqueda DuckDuckGo: {str(e)}'}
    
    def _search_duckduckgo_web(self, query: str, num_results: int) -> Dict:
        """
        Búsqueda web usando DuckDuckGo (requiere librería duckduckgo-search)
        """
        try:
            # Intentar usar duckduckgo-search si está disponible
            try:
                from duckduckgo_search import DDGS
                
                with DDGS() as ddgs:
                    results = []
                    for r in ddgs.text(query, max_results=num_results):
                        results.append({
                            'title': r.get('title', ''),
                            'snippet': r.get('body', ''),
                            'url': r.get('href', ''),
                            'source': 'DuckDuckGo Web'
                        })
                    
                    return {
                        'query': query,
                        'results': results,
                        'timestamp': datetime.now().isoformat(),
                        'engine': 'duckduckgo_web'
                    }
            except ImportError:
                # Si no está instalado, retornar error
                return {
                    'error': 'Librería duckduckgo-search no instalada. Instala con: pip install duckduckgo-search',
                    'query': query,
                    'results': []
                }
        except Exception as e:
            return {'error': f'Error en búsqueda web: {str(e)}'}
    
    def _search_google(self, query: str, num_results: int) -> Dict:
        """
        Búsqueda usando Google Custom Search API
        Requiere API key y Search Engine ID
        """
        if not self.api_key:
            return {'error': 'Google API key no configurada'}
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,  # Necesitas configurar esto
                'q': query,
                'num': min(num_results, 10)  # Google limita a 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            for item in data.get('items', [])[:num_results]:
                results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'url': item.get('link', ''),
                    'source': 'Google'
                })
            
            return {
                'query': query,
                'results': results,
                'timestamp': datetime.now().isoformat(),
                'engine': 'google'
            }
        except Exception as e:
            return {'error': f'Error en búsqueda Google: {str(e)}'}
    
    def search_trading_news(self, symbol: str = None) -> Dict:
        """
        Busca noticias de trading específicas
        """
        if symbol:
            query = f"noticias trading {symbol} mercado financiero"
        else:
            query = "noticias trading mercado financiero actuales"
        
        return self.search(query, num_results=5)
    
    def search_strategy_info(self, strategy_name: str) -> Dict:
        """
        Busca información sobre una estrategia específica
        """
        query = f"estrategia trading {strategy_name} análisis técnico"
        return self.search(query, num_results=5)
    
    def search_market_analysis(self, topic: str) -> Dict:
        """
        Busca análisis de mercado sobre un tema
        """
        query = f"análisis mercado {topic} trading"
        return self.search(query, num_results=5)

