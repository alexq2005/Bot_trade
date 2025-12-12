"""
News Fetcher Service
Obtiene noticias financieras desde múltiples APIs automáticamente.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
import time
import feedparser
from bs4 import BeautifulSoup

from src.core.logger import get_logger

logger = get_logger("news_fetcher")


class NewsAPIClient:
    """
    Cliente para NewsAPI (newsapi.org)
    Tier gratuito: 100 requests/día
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2"
    
    def get_news(self, symbol: str, days: int = 7, max_results: int = 10) -> List[Dict]:
        """Obtiene noticias para un símbolo"""
        if not self.api_key:
            logger.warning("NewsAPI key no configurada")
            return []
        
        try:
            # Limpiar símbolo
            clean_symbol = symbol.replace('.BA', '').replace('.AR', '')
            
            # Buscar noticias financieras
            endpoint = f"{self.base_url}/everything"
            params = {
                'q': f"{clean_symbol} stock OR {clean_symbol} shares OR {clean_symbol} company",
                'language': 'es,en',
                'sortBy': 'publishedAt',
                'pageSize': max_results,
                'apiKey': self.api_key,
                'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.warning(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                return []
            
            articles = []
            for article in data.get('articles', []):
                articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('content', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'published_at': article.get('publishedAt', ''),
                    'symbol': symbol
                })
            
            logger.info(f"✅ Obtenidas {len(articles)} noticias desde NewsAPI para {symbol}")
            return articles
        
        except Exception as e:
            logger.error(f"Error obteniendo noticias desde NewsAPI para {symbol}: {e}")
            return []


class AlphaVantageNewsClient:
    """
    Cliente para Alpha Vantage News API
    Requiere API key (gratis)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_news(self, symbol: str, days: int = 7, max_results: int = 10) -> List[Dict]:
        """Obtiene noticias desde Alpha Vantage"""
        if not self.api_key:
            logger.warning("Alpha Vantage API key no configurada")
            return []
        
        try:
            # Limpiar símbolo
            clean_symbol = symbol.replace('.BA', '').replace('.AR', '')
            
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': clean_symbol,
                'apikey': self.api_key,
                'limit': max_results
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data or 'Note' in data:
                logger.warning(f"Alpha Vantage News error: {data.get('Error Message', data.get('Note', 'Unknown error'))}")
                return []
            
            articles = []
            for item in data.get('feed', []):
                articles.append({
                    'title': item.get('title', ''),
                    'description': item.get('summary', ''),
                    'content': item.get('summary', ''),
                    'url': item.get('url', ''),
                    'source': item.get('source', 'Unknown'),
                    'published_at': item.get('time_published', ''),
                    'symbol': symbol,
                    'sentiment_score': item.get('overall_sentiment_score', 0)
                })
            
            logger.info(f"✅ Obtenidas {len(articles)} noticias desde Alpha Vantage para {symbol}")
            return articles
        
        except Exception as e:
            logger.error(f"Error obteniendo noticias desde Alpha Vantage para {symbol}: {e}")
            return []


class FinnhubNewsClient:
    """
    Cliente para Finnhub News API
    Tier gratuito: 60 calls/min
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
    
    def get_news(self, symbol: str, days: int = 7, max_results: int = 10) -> List[Dict]:
        """Obtiene noticias desde Finnhub"""
        if not self.api_key:
            logger.warning("Finnhub API key no configurada")
            return []
        
        try:
            # Limpiar símbolo
            clean_symbol = symbol.replace('.BA', '').replace('.AR', '')
            
            endpoint = f"{self.base_url}/company-news"
            params = {
                'symbol': clean_symbol,
                'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
                'to': datetime.now().strftime('%Y-%m-%d'),
                'token': self.api_key
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, list):
                logger.warning(f"Finnhub News error: {data.get('error', 'Unknown error')}")
                return []
            
            articles = []
            for item in data[:max_results]:
                articles.append({
                    'title': item.get('headline', ''),
                    'description': item.get('summary', ''),
                    'content': item.get('summary', ''),
                    'url': item.get('url', ''),
                    'source': item.get('source', 'Unknown'),
                    'published_at': item.get('datetime', 0),
                    'symbol': symbol
                })
            
            logger.info(f"✅ Obtenidas {len(articles)} noticias desde Finnhub para {symbol}")
            return articles
        
        except Exception as e:
            logger.error(f"Error obteniendo noticias desde Finnhub para {symbol}: {e}")
            return []


class RSSNewsClient:
    """
    Cliente para obtener noticias desde RSS feeds (100% GRATIS, sin API key).
    """
    
    def __init__(self):
        # RSS feeds de noticias financieras
        self.rss_feeds = {
            'argentina': [
                'https://www.infobae.com/feeds/rss/economia/',
                'https://www.lanacion.com.ar/rss/economia',
                'https://www.ambito.com/rss/economia',
                'https://www.cronista.com/rss/economia',
            ],
            'global': [
                'https://feeds.reuters.com/reuters/businessNews',
                'https://feeds.bloomberg.com/markets/news.rss',
                'https://www.cnbc.com/id/100003114/device/rss/rss.html',
                'https://feeds.feedburner.com/FinancialTimes',
            ]
        }
    
    def get_news(self, symbol: str, days: int = 7, max_results: int = 10) -> List[Dict]:
        """Obtiene noticias desde RSS feeds"""
        try:
            clean_symbol = symbol.replace('.BA', '').replace('.AR', '')
            all_articles = []
            
            # Intentar feeds argentinos primero para símbolos argentinos
            feeds_to_check = self.rss_feeds['argentina'] if '.BA' in symbol or symbol in ['GGAL', 'YPFD', 'PAMP'] else self.rss_feeds['global']
            feeds_to_check.extend(self.rss_feeds['global'])  # También buscar en globales
            
            for feed_url in feeds_to_check[:4]:  # Limitar a 4 feeds para no sobrecargar
                try:
                    feed = feedparser.parse(feed_url)
                    
                    for entry in feed.entries[:max_results]:
                        # Verificar si la noticia menciona el símbolo
                        title = entry.get('title', '').lower()
                        summary = entry.get('summary', '').lower()
                        content = f"{title} {summary}"
                        
                        if clean_symbol.lower() in content or symbol.lower() in content:
                            # Extraer contenido HTML si existe
                            description = entry.get('summary', '')
                            if hasattr(entry, 'content'):
                                description = entry.content[0].value if entry.content else description
                            
                            # Limpiar HTML
                            soup = BeautifulSoup(description, 'html.parser')
                            clean_description = soup.get_text()
                            
                            all_articles.append({
                                'title': entry.get('title', ''),
                                'description': clean_description[:500],  # Limitar tamaño
                                'content': clean_description,
                                'url': entry.get('link', ''),
                                'source': feed.feed.get('title', 'RSS Feed'),
                                'published_at': entry.get('published', ''),
                                'symbol': symbol
                            })
                            
                            if len(all_articles) >= max_results:
                                break
                    
                    if len(all_articles) >= max_results:
                        break
                    
                    time.sleep(0.5)  # Delay entre feeds
                
                except Exception as e:
                    logger.debug(f"Error parseando feed {feed_url}: {e}")
                    continue
            
            if all_articles:
                logger.info(f"✅ Obtenidas {len(all_articles)} noticias desde RSS para {symbol}")
            else:
                logger.debug(f"No se encontraron noticias en RSS para {symbol}")
            
            return all_articles[:max_results]
        
        except Exception as e:
            logger.error(f"Error obteniendo noticias desde RSS para {symbol}: {e}")
            return []


class NewsDataClient:
    """
    Cliente para NewsData.io API
    Plan gratuito disponible con límites
    Más de 85,000 fuentes en 206 países, 89 idiomas
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('NEWSDATA_API_KEY')
        self.base_url = "https://newsdata.io/api/1"
    
    def get_news(self, symbol: str, days: int = 7, max_results: int = 10) -> List[Dict]:
        """Obtiene noticias desde NewsData.io"""
        if not self.api_key:
            logger.warning("NewsData.io API key no configurada")
            return []
        
        try:
            # Limpiar símbolo
            clean_symbol = symbol.replace('.BA', '').replace('.AR', '')
            
            # Construir query de búsqueda
            query = f"{clean_symbol} stock OR {clean_symbol} shares OR {clean_symbol} company"
            
            endpoint = f"{self.base_url}/news"
            params = {
                'apikey': self.api_key,
                'q': query,
                'language': 'es,en',
                'category': 'business,finance',
                'size': max_results
            }
            
            # Si days > 0, intentar obtener noticias recientes
            if days > 0:
                # NewsData.io tiene un endpoint para noticias recientes
                # El parámetro 'timeframe' puede ser '24h', '7d', '30d', etc.
                if days <= 1:
                    params['timeframe'] = '24h'
                elif days <= 7:
                    params['timeframe'] = '7d'
                elif days <= 30:
                    params['timeframe'] = '30d'
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') != 'success':
                error_msg = data.get('message', 'Unknown error')
                logger.warning(f"NewsData.io error: {error_msg}")
                return []
            
            articles = []
            for article in data.get('results', [])[:max_results]:
                # NewsData.io estructura
                articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('content', '') or article.get('description', ''),
                    'url': article.get('link', ''),
                    'source': article.get('source_id', 'Unknown'),
                    'published_at': article.get('pubDate', ''),
                    'symbol': symbol,
                    'category': article.get('category', []),
                    'country': article.get('country', [])
                })
            
            logger.info(f"✅ Obtenidas {len(articles)} noticias desde NewsData.io para {symbol}")
            return articles
        
        except Exception as e:
            logger.error(f"Error obteniendo noticias desde NewsData.io para {symbol}: {e}")
            return []


class GoogleNewsClient:
    """
    Cliente para obtener noticias desde Google News (100% GRATIS, sin API key).
    Usa scraping básico de búsqueda de Google News.
    """
    
    def __init__(self):
        self.base_url = "https://news.google.com/rss"
    
    def get_news(self, symbol: str, days: int = 7, max_results: int = 10) -> List[Dict]:
        """Obtiene noticias desde Google News RSS"""
        try:
            clean_symbol = symbol.replace('.BA', '').replace('.AR', '')
            
            # Construir query de búsqueda
            query = f"{clean_symbol} stock OR {clean_symbol} shares OR {clean_symbol} company"
            query_encoded = requests.utils.quote(query)
            
            # URL de Google News RSS
            rss_url = f"{self.base_url}/search?q={query_encoded}&hl=es&gl=AR&ceid=AR:es"
            
            feed = feedparser.parse(rss_url)
            
            articles = []
            for entry in feed.entries[:max_results]:
                # Extraer información
                title = entry.get('title', '')
                # Google News RSS a veces tiene el título con fuente, limpiarlo
                if ' - ' in title:
                    title = title.split(' - ')[0]
                
                description = entry.get('summary', '')
                soup = BeautifulSoup(description, 'html.parser')
                clean_description = soup.get_text()
                
                articles.append({
                    'title': title,
                    'description': clean_description[:500],
                    'content': clean_description,
                    'url': entry.get('link', ''),
                    'source': entry.get('source', {}).get('title', 'Google News') if hasattr(entry, 'source') else 'Google News',
                    'published_at': entry.get('published', ''),
                    'symbol': symbol
                })
            
            if articles:
                logger.info(f"✅ Obtenidas {len(articles)} noticias desde Google News para {symbol}")
            
            return articles
        
        except Exception as e:
            logger.error(f"Error obteniendo noticias desde Google News para {symbol}: {e}")
            return []


class NewsFetcher:
    """
    Servicio unificado para obtener noticias desde múltiples fuentes.
    
    Orden de prioridad:
    1. NewsAPI (100 requests/día gratis, requiere API key)
    2. NewsData.io (plan gratuito disponible, requiere API key) ← NUEVO
    3. Alpha Vantage News (requiere API key)
    4. Finnhub News (requiere API key)
    5. Google News RSS (100% GRATIS, sin API key)
    6. RSS Feeds (100% GRATIS, sin API key)
    """
    
    def __init__(self):
        self.news_api = NewsAPIClient() if os.getenv('NEWS_API_KEY') else None
        self.newsdata = NewsDataClient() if os.getenv('NEWSDATA_API_KEY') else None
        self.alpha_vantage = AlphaVantageNewsClient() if os.getenv('ALPHA_VANTAGE_API_KEY') else None
        self.finnhub = FinnhubNewsClient() if os.getenv('FINNHUB_API_KEY') else None
        self.google_news = GoogleNewsClient()  # Siempre disponible (gratis)
        self.rss_client = RSSNewsClient()  # Siempre disponible (gratis)
        
        self.sources = []
        # Fuentes que requieren API key (mayor prioridad)
        if self.news_api:
            self.sources.append(('NewsAPI', self._get_from_newsapi))
        if self.newsdata:
            self.sources.append(('NewsData.io', self._get_from_newsdata))
        if self.alpha_vantage:
            self.sources.append(('Alpha Vantage', self._get_from_alpha_vantage))
        if self.finnhub:
            self.sources.append(('Finnhub', self._get_from_finnhub))
        
        # Fuentes gratuitas sin API key (fallback)
        self.sources.append(('Google News', self._get_from_google_news))
        self.sources.append(('RSS Feeds', self._get_from_rss))
    
    def _get_from_newsapi(self, symbol: str, days: int, max_results: int) -> List[Dict]:
        """Wrapper para NewsAPI"""
        return self.news_api.get_news(symbol, days, max_results) if self.news_api else []
    
    def _get_from_newsdata(self, symbol: str, days: int, max_results: int) -> List[Dict]:
        """Wrapper para NewsData.io"""
        return self.newsdata.get_news(symbol, days, max_results) if self.newsdata else []
    
    def _get_from_alpha_vantage(self, symbol: str, days: int, max_results: int) -> List[Dict]:
        """Wrapper para Alpha Vantage"""
        return self.alpha_vantage.get_news(symbol, days, max_results) if self.alpha_vantage else []
    
    def _get_from_finnhub(self, symbol: str, days: int, max_results: int) -> List[Dict]:
        """Wrapper para Finnhub"""
        return self.finnhub.get_news(symbol, days, max_results) if self.finnhub else []
    
    def _get_from_google_news(self, symbol: str, days: int, max_results: int) -> List[Dict]:
        """Wrapper para Google News"""
        return self.google_news.get_news(symbol, days, max_results)
    
    def _get_from_rss(self, symbol: str, days: int, max_results: int) -> List[Dict]:
        """Wrapper para RSS Feeds"""
        return self.rss_client.get_news(symbol, days, max_results)
    
    def get_news(self, symbol: str, days: int = 7, max_results: int = 10) -> List[Dict]:
        """
        Obtiene noticias intentando múltiples fuentes.
        
        Args:
            symbol: Símbolo a buscar
            days: Días hacia atrás para buscar noticias
            max_results: Máximo de noticias a retornar
        
        Returns:
            Lista de noticias (puede estar vacía si no hay fuentes configuradas)
        """
        all_news = []
        
        # Intentar todas las fuentes disponibles
        for source_name, source_func in self.sources:
            try:
                logger.info(f"Obteniendo noticias desde {source_name} para {symbol}...")
                news = source_func(symbol, days, max_results)
                
                if news:
                    all_news.extend(news)
                    logger.info(f"✅ {len(news)} noticias obtenidas desde {source_name}")
                    
                    # Si ya tenemos suficientes noticias, parar
                    if len(all_news) >= max_results:
                        break
                
                # Delay para no sobrecargar APIs
                time.sleep(0.5)
            
            except Exception as e:
                logger.warning(f"Error con {source_name} para {symbol}: {e}")
                continue
        
        # Eliminar duplicados (por título)
        seen_titles = set()
        unique_news = []
        for article in all_news:
            title = article.get('title', '').lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(article)
        
        # Limitar resultados
        unique_news = unique_news[:max_results]
        
        if unique_news:
            logger.info(f"✅ Total: {len(unique_news)} noticias únicas obtenidas para {symbol}")
        else:
            logger.warning(f"⚠️ No se obtuvieron noticias para {symbol} desde ninguna fuente")
        
        return unique_news
    
    def get_available_sources(self) -> List[str]:
        """Retorna lista de fuentes disponibles"""
        return [name for name, _ in self.sources]
    
    def get_source_info(self) -> Dict[str, Dict]:
        """Retorna información sobre cada fuente"""
        info = {
            'NewsAPI': {
                'free': True,
                'api_key_required': True,
                'rate_limit': '100 requests/día',
                'coverage': 'Global',
                'signup': 'https://newsapi.org/register'
            },
            'NewsData.io': {
                'free': True,
                'api_key_required': True,
                'rate_limit': 'Plan gratuito con límites',
                'coverage': '85,000+ fuentes, 206 países, 89 idiomas',
                'signup': 'https://newsdata.io/'
            },
            'Alpha Vantage': {
                'free': True,
                'api_key_required': True,
                'rate_limit': '5 calls/min, 500 calls/día',
                'coverage': 'Global (principalmente USA)',
                'signup': 'https://www.alphavantage.co/support/#api-key'
            },
            'Finnhub': {
                'free': True,
                'api_key_required': True,
                'rate_limit': '60 calls/min',
                'coverage': 'Global',
                'signup': 'https://finnhub.io/register'
            },
            'Google News': {
                'free': True,
                'api_key_required': False,
                'rate_limit': 'Sin límite oficial (usar con moderación)',
                'coverage': 'Global',
                'signup': 'No requiere registro'
            },
            'RSS Feeds': {
                'free': True,
                'api_key_required': False,
                'rate_limit': 'Sin límite oficial (usar con moderación)',
                'coverage': 'Argentina y Global',
                'signup': 'No requiere registro'
            }
        }
        
        return {k: v for k, v in info.items() if k in self.get_available_sources()}


if __name__ == "__main__":
    # Test del servicio
    fetcher = NewsFetcher()
    
    print("Fuentes de noticias disponibles:")
    for source in fetcher.get_available_sources():
        print(f"  - {source}")
    
    if not fetcher.get_available_sources():
        print("\n⚠️ No hay fuentes configuradas. Configura al menos una API key:")
        print("  - NEWS_API_KEY")
        print("  - NEWSDATA_API_KEY")
        print("  - ALPHA_VANTAGE_API_KEY")
        print("  - FINNHUB_API_KEY")
        print("\nO usa las fuentes gratuitas (Google News, RSS) que no requieren API key.")
    else:
        print("\nProbando obtención de noticias para AAPL...")
        news = fetcher.get_news("AAPL", days=7, max_results=5)
        print(f"\nNoticias obtenidas: {len(news)}")
        for i, article in enumerate(news, 1):
            print(f"\n{i}. {article.get('title', 'Sin título')}")
            print(f"   Fuente: {article.get('source', 'Unknown')}")
            print(f"   Fecha: {article.get('published_at', 'Unknown')}")

