"""
Chat Interface - Interfaz de chat interactiva con el bot
Permite comunicación espontánea y razonamiento
"""
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from src.services.advanced_reasoning_agent import AdvancedReasoningAgent
from src.services.web_search_agent import WebSearchAgent


class ChatInterface:
    """
    Interfaz de chat interactiva con el bot
    """
    
    def __init__(self, bot_directory: str = ".", telegram_bot=None, trading_bot=None):
        self.bot_directory = Path(bot_directory)
        self.telegram_bot = telegram_bot
        self.trading_bot = trading_bot  # Referencia al bot de trading para retroalimentación
        
        # Inicializar agentes
        self.reasoning_agent = AdvancedReasoningAgent(bot_directory=str(bot_directory))
        self.web_search_agent = WebSearchAgent()
        
        # Estado del chat
        self.active = True
        self.last_interaction = None
        
        # Memoria compartida con el bot de trading
        self.shared_memory_file = self.bot_directory / "data" / "shared_learning.json"
        
    def process_message(self, message: str, user_id: str = "default", context: Dict = None) -> str:
        """
        Procesa un mensaje y genera respuesta
        
        Args:
            message: Mensaje del usuario
            user_id: ID del usuario
            context: Contexto adicional (trades, métricas, etc.)
            
        Returns:
            Respuesta del bot
        """
        try:
            # Razonar sobre el mensaje
            reasoning = self.reasoning_agent.reason_about_message(message, context)
            
            # Si necesita búsqueda web, buscar información
            web_info = None
            if reasoning.get('needs_web_search') and reasoning.get('search_query'):
                try:
                    print(f"🔍 Buscando información: {reasoning['search_query']}")
                    web_info = self.web_search_agent.search(reasoning['search_query'])
                    # Si hay error en la búsqueda, continuar sin web_info
                    if web_info and web_info.get('error'):
                        print(f"⚠️ Error en búsqueda web: {web_info.get('error')}")
                        web_info = None
                    elif web_info and web_info.get('results'):
                        # APRENDER de la búsqueda web - guardar información encontrada
                        self._learn_from_web_search(reasoning['search_query'], web_info)
                except Exception as e:
                    print(f"⚠️ Error ejecutando búsqueda web: {e}")
                    web_info = None  # Continuar sin búsqueda web
            
            # Generar respuesta
            try:
                response = self.reasoning_agent.generate_response(reasoning, web_info)
                
                # Asegurar que siempre hay una respuesta
                if not response or response.strip() == "":
                    response = self._generate_fallback_response(message, reasoning)
                
            except Exception as e:
                print(f"⚠️ Error generando respuesta: {e}")
                response = self._generate_fallback_response(message, reasoning)
            
            # Pensamientos espontáneos (ocasionalmente)
            try:
                if self.reasoning_agent.think_spontaneously():
                    spontaneous_thought = self.reasoning_agent.think_spontaneously()
                    if spontaneous_thought:
                        response += f"\n\n💭 {spontaneous_thought}"
            except Exception:
                pass  # Ignorar errores en pensamientos espontáneos
            
            # Guardar interacción
            self.last_interaction = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'message': message,
                'response': response,
                'reasoning': reasoning,
                'web_search_performed': web_info is not None,
                'search_query': reasoning.get('search_query') if reasoning else None
            }
            
            # APRENDER de la interacción completa
            try:
                self.reasoning_agent.learn_from_interaction(message, response)
            except Exception as e:
                print(f"⚠️ Error aprendiendo de interacción: {e}")
            
            # COMPARTIR aprendizaje con el bot de trading
            try:
                self.share_learning_with_trading_bot(self.last_interaction)
            except Exception as e:
                print(f"⚠️ Error compartiendo aprendizaje: {e}")
            
            return response
            
        except Exception as e:
            # Fallback final si todo falla
            print(f"❌ Error crítico procesando mensaje: {e}")
            return f"Lo siento, tuve un problema procesando tu mensaje. ¿Podrías reformularlo? El error fue: {str(e)[:100]}"
    
    def _generate_fallback_response(self, message: str, reasoning: Dict = None) -> str:
        """Genera una respuesta de fallback cuando falla la generación normal"""
        message_lower = message.lower()
        
        # Respuestas contextuales según el mensaje
        if any(word in message_lower for word in ['hola', 'hi', 'hello', 'buenos días', 'buenas tardes']):
            return "¡Hola! Estoy aquí para ayudarte. ¿En qué puedo asistirte hoy?"
        
        elif any(word in message_lower for word in ['trading', 'operar', 'comprar', 'vender']):
            return "Sobre trading, puedo ayudarte con:\n• Análisis de mercado\n• Estrategias de trading\n• Gestión de riesgo\n• Optimización de parámetros\n\n¿Qué te gustaría saber específicamente?"
        
        elif any(word in message_lower for word in ['precio', 'cotización', 'valor']):
            return "Para consultar precios y cotizaciones, puedes usar el Dashboard en Vivo o el Terminal de Trading. ¿Hay algún activo específico que te interese?"
        
        elif '?' in message or any(word in message_lower for word in ['qué', 'cómo', 'cuándo', 'dónde', 'por qué']):
            return f"Interesante pregunta sobre '{message[:50]}'. Déjame pensar...\n\nBasándome en mi conocimiento, puedo ayudarte con información sobre trading, análisis técnico, y estrategias. ¿Puedes ser más específico sobre lo que necesitas?"
        
        else:
            return f"Entiendo que mencionas '{message[:50]}'. Estoy aquí para ayudarte con:\n\n• Trading y análisis de mercado\n• Estrategias y optimización\n• Gestión de portafolio\n• Predicciones y señales\n\n¿Sobre qué aspecto específico te gustaría conversar?"
    
    def _learn_from_web_search(self, query: str, web_info: Dict):
        """
        Aprende y guarda información de búsquedas web en la memoria del bot
        """
        try:
            if not web_info or not web_info.get('results'):
                return
            
            # Extraer información útil de los resultados
            learned_facts = []
            for result in web_info.get('results', [])[:3]:  # Top 3 resultados
                fact = {
                    'query': query,
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'url': result.get('url', ''),
                    'source': result.get('source', 'web'),
                    'timestamp': datetime.now().isoformat(),
                    'type': 'web_search_result'
                }
                learned_facts.append(fact)
            
            # Guardar en memoria del reasoning agent
            if hasattr(self.reasoning_agent, 'memory'):
                if 'facts' not in self.reasoning_agent.memory:
                    self.reasoning_agent.memory['facts'] = []
                
                # Agregar hechos aprendidos de la web
                for fact in learned_facts:
                    # Verificar si ya existe información similar (evitar duplicados)
                    existing = [f for f in self.reasoning_agent.memory['facts'] 
                              if f.get('query') == query and f.get('type') == 'web_search_result']
                    if not existing:
                        self.reasoning_agent.memory['facts'].append(fact)
                        print(f"📚 Aprendido de web: {fact.get('title', 'N/A')[:50]}")
                
                # Limitar tamaño de memoria (mantener últimos 1000 hechos)
                if len(self.reasoning_agent.memory['facts']) > 1000:
                    self.reasoning_agent.memory['facts'] = self.reasoning_agent.memory['facts'][-1000:]
                
                # Guardar memoria
                self.reasoning_agent._save_memory()
                
                # Actualizar intereses basado en la búsqueda
                if query:
                    query_words = query.lower().split()
                    for word in query_words:
                        if len(word) > 3:  # Ignorar palabras muy cortas
                            if word not in self.reasoning_agent.interests['topics']:
                                self.reasoning_agent.interests['topics'][word] = {'count': 0, 'last_mentioned': None}
                            self.reasoning_agent.interests['topics'][word]['count'] += 1
                            self.reasoning_agent.interests['topics'][word]['last_mentioned'] = datetime.now().isoformat()
                    
                    self.reasoning_agent._update_interest_priorities()
                    self.reasoning_agent._save_interests()
                    
        except Exception as e:
            print(f"⚠️ Error aprendiendo de búsqueda web: {e}")
    
    def _get_trading_bot_context(self) -> Dict:
        """
        Obtiene contexto del bot de trading para retroalimentación
        """
        context = {}
        
        try:
            # 1. Cargar trades recientes
            trades_file = Path("data/trades.json")
            if trades_file.exists():
                with open(trades_file, 'r', encoding='utf-8') as f:
                    trades = json.load(f)
                    if trades:
                        context['recent_trades'] = trades[-10:]  # Últimos 10 trades
                        context['total_trades'] = len(trades)
                        
                        # Calcular métricas
                        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
                        context['win_rate'] = len(winning_trades) / len(trades) if trades else 0
                        context['total_pnl'] = sum(t.get('pnl', 0) for t in trades)
            
            # 2. Cargar portfolio
            portfolio_file = Path("data/portfolio.json")
            if portfolio_file.exists():
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    portfolio_data = json.load(f)
                    context['portfolio'] = portfolio_data
                    if isinstance(portfolio_data, list):
                        context['portfolio_size'] = len(portfolio_data)
            
            # 3. Cargar operaciones recientes
            operations_file = Path("data/operations_log.json")
            if operations_file.exists():
                with open(operations_file, 'r', encoding='utf-8') as f:
                    operations = json.load(f)
                    if operations:
                        context['recent_operations'] = operations[-20:]  # Últimas 20 operaciones
            
            # 4. Verificar estado del bot
            bot_pid_file = Path("bot.pid")
            context['bot_running'] = bot_pid_file.exists()
            
            # 5. Cargar aprendizaje compartido del bot de trading
            shared_learning = self._load_shared_learning()
            if shared_learning:
                context['shared_insights'] = shared_learning.get('insights', [])
                context['shared_patterns'] = shared_learning.get('patterns', [])
                # Agregar patrones y insights del bot de trading
                context['trading_patterns'] = shared_learning.get('trading_patterns', [])
                context['trading_insights'] = shared_learning.get('trading_insights', [])
            
        except Exception as e:
            print(f"⚠️ Error obteniendo contexto del bot: {e}")
        
        return context
    
    def _load_shared_learning(self) -> Dict:
        """Carga aprendizaje compartido entre chat y bot de trading"""
        if self.shared_memory_file.exists():
            try:
                with open(self.shared_memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_shared_learning(self, learning_data: Dict):
        """Guarda aprendizaje para compartir con el bot de trading"""
        try:
            current = self._load_shared_learning()
            
            # Agregar nuevos insights
            if 'insights' not in current:
                current['insights'] = []
            if 'insights' in learning_data:
                current['insights'].extend(learning_data['insights'])
                # Mantener solo los últimos 100 insights
                current['insights'] = current['insights'][-100:]
            
            # Agregar nuevos patrones
            if 'patterns' not in current:
                current['patterns'] = []
            if 'patterns' in learning_data:
                current['patterns'].extend(learning_data['patterns'])
                current['patterns'] = current['patterns'][-50:]
            
            # Agregar conocimiento aprendido del chat
            if 'chat_knowledge' not in current:
                current['chat_knowledge'] = []
            if 'chat_knowledge' in learning_data:
                current['chat_knowledge'].extend(learning_data['chat_knowledge'])
                current['chat_knowledge'] = current['chat_knowledge'][-200:]
            
            current['last_updated'] = datetime.now().isoformat()
            
            # Guardar
            self.shared_memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.shared_memory_file, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            print(f"⚠️ Error guardando aprendizaje compartido: {e}")
    
    def share_learning_with_trading_bot(self, interaction_data: Dict):
        """
        Comparte aprendizaje del chat con el bot de trading
        """
        try:
            # Extraer conocimiento útil de la interacción
            learning_data = {
                'insights': [],
                'patterns': [],
                'chat_knowledge': []
            }
            
            # Si la conversación fue sobre trading, extraer insights
            message = interaction_data.get('message', '').lower()
            response = interaction_data.get('response', '')
            
            trading_keywords = ['trading', 'estrategia', 'win rate', 'mejor', 'optimizar', 'mejorar']
            if any(keyword in message for keyword in trading_keywords):
                # Extraer insights del razonamiento
                reasoning = interaction_data.get('reasoning', {})
                if reasoning.get('logical_analysis'):
                    insight = {
                        'type': 'chat_insight',
                        'topic': ' '.join(reasoning.get('topics', [])),
                        'message': message[:200],
                        'timestamp': datetime.now().isoformat()
                    }
                    learning_data['insights'].append(insight)
            
            # Guardar conocimiento aprendido de búsquedas web
            if interaction_data.get('web_search_performed'):
                knowledge = {
                    'type': 'web_knowledge',
                    'query': interaction_data.get('search_query', ''),
                    'timestamp': datetime.now().isoformat()
                }
                learning_data['chat_knowledge'].append(knowledge)
            
            # Guardar en memoria compartida
            if learning_data['insights'] or learning_data['patterns'] or learning_data['chat_knowledge']:
                self._save_shared_learning(learning_data)
                print(f"📤 Compartiendo {len(learning_data['insights'])} insights con el bot de trading")
                
        except Exception as e:
            print(f"⚠️ Error compartiendo aprendizaje: {e}")
    
    def start_conversation(self) -> str:
        """Inicia una conversación"""
        greetings = [
            "¡Hola! Soy tu bot de trading. Puedo razonar, buscar información y mejorar basado en nuestros intereses. ¿En qué puedo ayudarte?",
            "Hola, estoy aquí para conversar contigo. Puedo ayudarte con trading, buscar información en internet, o simplemente charlar. ¿Qué te gustaría hacer?",
            "¡Hola! Me alegra hablar contigo. Tengo capacidad de razonamiento y puedo acceder a información de internet. ¿Sobre qué quieres conversar?"
        ]
        
        import random
        return random.choice(greetings)
    
    def get_bot_status(self) -> str:
        """Obtiene estado actual del bot"""
        interests = self.reasoning_agent.get_current_interests()
        
        status = "🤖 **Estado del Bot:**\n\n"
        status += "**Intereses actuales:**\n"
        if interests:
            for i, interest in enumerate(interests[:5], 1):
                status += f"{i}. {interest}\n"
        else:
            status += "Aún no tengo intereses específicos\n"
        
        status += "\n**Pensamientos recientes:**\n"
        recent_thoughts = self.reasoning_agent.recent_thoughts[-3:]
        if recent_thoughts:
            for thought in recent_thoughts:
                status += f"• {thought['thought']}\n"
        else:
            status += "Ninguno reciente\n"
        
        return status
    
    def suggest_improvements(self) -> str:
        """Sugiere mejoras basadas en intereses"""
        improvements = self.reasoning_agent.suggest_improvements_based_on_interests()
        
        if not improvements:
            return "No tengo sugerencias de mejora en este momento. ¿Hay algo específico que te gustaría que mejore?"
        
        response = "💡 **Sugerencias de mejora basadas en mis intereses:**\n\n"
        for imp in improvements:
            response += f"• **{imp['interest']}**: {imp['suggestion']} (Prioridad: {imp['priority']})\n"
        
        return response
    
    def handle_telegram_message(self, update):
        """
        Maneja mensajes de Telegram
        """
        try:
            message = update.message.text
            user_id = str(update.message.from_user.id)
            
            # Procesar mensaje
            response = self.process_message(message, user_id)
            
            # Enviar respuesta
            if self.telegram_bot:
                self.telegram_bot.send_message(user_id, response)
            else:
                print(f"Respuesta: {response}")
            
        except Exception as e:
            error_msg = f"Error procesando mensaje de Telegram: {e}"
            print(error_msg)
            if self.telegram_bot:
                self.telegram_bot.send_message(user_id, "Lo siento, hubo un error procesando tu mensaje. ¿Puedes intentar de nuevo?")
    
    def interactive_chat(self):
        """
        Modo de chat interactivo por consola
        """
        print("\n" + "="*60)
        print("💬 CHAT INTERACTIVO CON EL BOT")
        print("="*60)
        print("\nEscribe 'salir' para terminar la conversación")
        print("Escribe 'estado' para ver el estado del bot")
        print("Escribe 'mejoras' para ver sugerencias de mejora")
        print("\n" + self.start_conversation() + "\n")
        
        while self.active:
            try:
                user_input = input("\nTú: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['salir', 'exit', 'quit']:
                    print("\n👋 ¡Hasta luego! Fue un placer conversar contigo.")
                    break
                
                elif user_input.lower() == 'estado':
                    print(f"\n{self.get_bot_status()}")
                    continue
                
                elif user_input.lower() == 'mejoras':
                    print(f"\n{self.suggest_improvements()}")
                    continue
                
                # Procesar mensaje
                response = self.process_message(user_input)
                print(f"\nBot: {response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Conversación terminada.")
                break
            except Exception as e:
                print(f"\n⚠️  Error: {e}")
                print("Intenta de nuevo o escribe 'salir' para terminar.")

