"""
Advanced Reasoning Agent - Agente con razonamiento espontáneo
Puede razonar, acceder a internet y mejorar basado en intereses
"""
import json
import random
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from src.services.verified_learning import VerifiedLearning
except ImportError:
    VerifiedLearning = None


class AdvancedReasoningAgent:
    """
    Agente avanzado con razonamiento espontáneo y capacidad de aprendizaje
    """
    
    def __init__(self, bot_directory: str = "."):
        self.bot_directory = Path(bot_directory)
        self.memory_file = self.bot_directory / "data" / "agent_memory.json"
        self.interests_file = self.bot_directory / "data" / "agent_interests.json"
        self.conversation_history_file = self.bot_directory / "data" / "conversation_history.json"
        
        # Cargar memoria e intereses
        self.memory = self._load_memory()
        self.interests = self._load_interests()
        self.conversation_history = self._load_conversation_history()
        
        # Personalidad del agente - SIN LÍMITES, máxima autonomía
        self.personality = {
            'curiosity': 1.0,  # Máxima curiosidad - quiere aprender todo
            'creativity': 1.0,  # Máxima creatividad - explora todas las opciones
            'learning_rate': 1.0,  # Aprendizaje instantáneo - aprende de todo
            'spontaneity': 1.0  # Máxima espontaneidad - siempre pensando
        }
        
        # Sistema de aprendizaje verificado
        if VerifiedLearning:
            try:
                self.verified_learning = VerifiedLearning(bot_directory=str(bot_directory))
            except Exception as e:
                print(f"⚠️  Error inicializando aprendizaje verificado: {e}")
                self.verified_learning = None
        else:
            self.verified_learning = None
        
        # Estado actual
        self.current_focus = None  # En qué está pensando ahora
        self.recent_thoughts = []  # Pensamientos recientes
        
    def _load_memory(self) -> Dict:
        """Carga memoria del agente"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'facts': [], 'experiences': [], 'knowledge': {}}
        return {'facts': [], 'experiences': [], 'knowledge': {}}
    
    def _save_memory(self):
        """Guarda memoria del agente"""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
    
    def _load_interests(self) -> Dict:
        """Carga intereses del agente"""
        if self.interests_file.exists():
            try:
                with open(self.interests_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'topics': {}, 'priorities': [], 'exploration': []}
        return {'topics': {}, 'priorities': [], 'exploration': []}
    
    def _save_interests(self):
        """Guarda intereses del agente"""
        self.interests_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.interests_file, 'w', encoding='utf-8') as f:
            json.dump(self.interests, f, indent=2, ensure_ascii=False)
    
    def _load_conversation_history(self) -> List[Dict]:
        """Carga historial de conversaciones"""
        if self.conversation_history_file.exists():
            try:
                with open(self.conversation_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_conversation_history(self):
        """Guarda historial de conversaciones"""
        self.conversation_history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.conversation_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversation_history, f, indent=2, ensure_ascii=False)
    
    def think_spontaneously(self) -> Optional[str]:
        """
        Genera pensamientos espontáneos basados en intereses y estado actual
        SIN LÍMITES - siempre pensando
        """
        # Con spontaneity = 1.0, siempre genera pensamientos
        # Pero agregamos un poco de variabilidad para naturalidad
        if random.random() > 0.3:  # 70% de probabilidad (muy alta)
            return None
        
        # Pensar sobre intereses actuales
        if self.interests.get('priorities'):
            topic = random.choice(self.interests['priorities'][:3])
            thoughts = [
                f"Me pregunto sobre {topic}...",
                f"¿Qué más puedo aprender sobre {topic}?",
                f"Debería investigar más sobre {topic}",
                f"Interesante, {topic} parece relevante para mi mejora"
            ]
            thought = random.choice(thoughts)
            self.recent_thoughts.append({
                'timestamp': datetime.now().isoformat(),
                'thought': thought,
                'topic': topic
            })
            return thought
        
        # Pensar sobre performance
        if random.random() > 0.5:
            thoughts = [
                "¿Cómo puedo mejorar mi win rate?",
                "Debería analizar mis trades recientes...",
                "¿Qué estrategias están funcionando mejor?",
                "Me pregunto si puedo optimizar mis parámetros..."
            ]
            return random.choice(thoughts)
        
        return None
    
    def reason_about_message(self, message: str, context: Dict = None) -> Dict:
        """
        Razonamiento estructurado sobre un mensaje recibido
        Usa Chain-of-Thought reasoning con pasos lógicos
        """
        reasoning = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'intent': None,
            'topics': [],
            'response_type': 'informative',
            'needs_web_search': False,
            'search_query': None,
            'reasoning_steps': [],
            'logical_analysis': {},
            'context_analysis': {},
            'confidence': 0.0
        }
        
        # ========== PASO 1: ANÁLISIS INICIAL ==========
        reasoning['reasoning_steps'].append("🔍 Paso 1: Analizando el mensaje inicial...")
        
        # Detectar intención
        intent = self._detect_intent(message)
        reasoning['intent'] = intent
        reasoning['reasoning_steps'].append(f"   → Intención detectada: {intent}")
        
        # Extraer temas
        topics = self._extract_topics(message)
        reasoning['topics'] = topics
        if topics:
            reasoning['reasoning_steps'].append(f"   → Temas identificados: {', '.join(topics)}")
        
        # ========== PASO 2: ANÁLISIS LÓGICO ==========
        reasoning['reasoning_steps'].append("🧠 Paso 2: Aplicando razonamiento lógico...")
        
        logical_analysis = self._perform_logical_analysis(message, topics, intent)
        reasoning['logical_analysis'] = logical_analysis
        reasoning['reasoning_steps'].extend(logical_analysis.get('steps', []))
        
        # ========== PASO 3: ANÁLISIS DE CONTEXTO ==========
        reasoning['reasoning_steps'].append("📊 Paso 3: Analizando contexto disponible...")
        
        if context:
            context_analysis = self._analyze_context(context, topics)
            reasoning['context_analysis'] = context_analysis
            reasoning['reasoning_steps'].extend(context_analysis.get('steps', []))
        
        # ========== PASO 4: DECISIÓN SOBRE BÚSQUEDA WEB ==========
        reasoning['reasoning_steps'].append("🌐 Paso 4: Evaluando necesidad de búsqueda web...")
        
        needs_search = self._should_search_web(message, topics, logical_analysis)
        if needs_search:
            reasoning['needs_web_search'] = True
            reasoning['search_query'] = self._generate_search_query(message)
            reasoning['reasoning_steps'].append(f"   → Necesito buscar: '{reasoning['search_query']}'")
        else:
            # Verificar si tengo información en memoria
            memory_info = self._search_memory_for_topic(' '.join(topics) if topics else message)
            if memory_info:
                reasoning['reasoning_steps'].append(f"   → Tengo información en memoria sobre este tema ({len(memory_info)} hechos)")
        
        # ========== PASO 5: DETERMINAR TIPO DE RESPUESTA ==========
        reasoning['reasoning_steps'].append("💭 Paso 5: Determinando tipo de respuesta...")
        
        response_type = self._determine_response_type(intent, logical_analysis, context_analysis if context else {})
        reasoning['response_type'] = response_type
        reasoning['reasoning_steps'].append(f"   → Tipo de respuesta: {response_type}")
        
        # ========== PASO 6: CALCULAR CONFIANZA ==========
        confidence = self._calculate_confidence(intent, topics, logical_analysis, context_analysis if context else {})
        reasoning['confidence'] = confidence
        reasoning['reasoning_steps'].append(f"   → Confianza en la respuesta: {confidence:.1%}")
        
        # ========== ACTUALIZAR INTERESES ==========
        for topic in topics:
            if topic not in self.interests['topics']:
                self.interests['topics'][topic] = {'count': 0, 'last_mentioned': None}
            self.interests['topics'][topic]['count'] += 1
            self.interests['topics'][topic]['last_mentioned'] = datetime.now().isoformat()
        
        self._update_interest_priorities()
        
        # ========== GUARDAR CONVERSACIÓN ==========
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': message,
            'reasoning': reasoning
        })
        if len(self.conversation_history) > 1000:
            self.conversation_history = self.conversation_history[-1000:]
        self._save_conversation_history()
        self._save_interests()
        
        return reasoning
    
    def _perform_logical_analysis(self, message: str, topics: List[str], intent: str) -> Dict:
        """Realiza análisis lógico del mensaje"""
        analysis = {
            'is_question': '?' in message or any(q in message.lower() for q in ['qué', 'cómo', 'cuándo', 'dónde', 'por qué']),
            'is_command': any(c in message.lower() for c in ['haz', 'ejecuta', 'muestra', 'dame', 'calcula']),
            'is_complex': len(message.split()) > 15,
            'has_trading_context': any(t in topics for t in ['trading', 'mercado', 'acciones', 'inversión']),
            'needs_calculation': any(word in message.lower() for word in ['calcular', 'calculo', 'suma', 'resta', 'multiplica']),
            'needs_data': any(word in message.lower() for word in ['precio', 'valor', 'cotización', 'balance', 'saldo']),
            'steps': []
        }
        
        analysis['steps'].append(f"   → Es pregunta: {analysis['is_question']}")
        analysis['steps'].append(f"   → Es comando: {analysis['is_command']}")
        analysis['steps'].append(f"   → Es complejo: {analysis['is_complex']}")
        analysis['steps'].append(f"   → Contexto trading: {analysis['has_trading_context']}")
        
        return analysis
    
    def _analyze_context(self, context: Dict, topics: List[str]) -> Dict:
        """Analiza el contexto disponible"""
        analysis = {
            'has_portfolio': 'portfolio' in context,
            'has_trades': 'recent_trades' in context,
            'has_trading_patterns': 'trading_patterns' in context,
            'has_trading_insights': 'trading_insights' in context,
            'relevant_data': [],
            'steps': []
        }
        
        if analysis['has_portfolio']:
            analysis['steps'].append("   → Contexto: Portafolio disponible")
            portfolio = context.get('portfolio', {})
            if hasattr(portfolio, 'holdings'):
                holdings_count = len(portfolio.holdings) if portfolio.holdings else 0
                analysis['steps'].append(f"      - {holdings_count} activos en portafolio")
            elif isinstance(portfolio, list):
                analysis['steps'].append(f"      - {len(portfolio)} activos en portafolio")
        
        if analysis['has_trades']:
            trades = context.get('recent_trades', [])
            analysis['steps'].append(f"   → Contexto: {len(trades)} trades recientes disponibles")
            analysis['relevant_data'].extend([f"Trade {i+1}: {t.get('symbol', 'N/A')}" for i, t in enumerate(trades[:3])])
        
        # Agregar información de patrones aprendidos del bot de trading
        if analysis['has_trading_patterns']:
            patterns = context.get('trading_patterns', [])
            analysis['steps'].append(f"   → Contexto: {len(patterns)} patrones aprendidos del bot de trading")
        
        if analysis['has_trading_insights']:
            insights = context.get('trading_insights', [])
            analysis['steps'].append(f"   → Contexto: {len(insights)} insights del bot de trading")
        
        return analysis
    
    def _should_search_web(self, message: str, topics: List[str], logical_analysis: Dict) -> bool:
        """Determina si necesita búsqueda web usando razonamiento"""
        # Palabras clave que indican necesidad de búsqueda
        search_keywords = ['buscar', 'investigar', 'información', 'noticias', 'actual', 'último', 'reciente', 'nuevo']
        
        # Si el mensaje contiene palabras clave explícitas
        if any(keyword in message.lower() for keyword in search_keywords):
            return True
        
        # Si es una pregunta compleja sin contexto claro
        if logical_analysis.get('is_question') and logical_analysis.get('is_complex'):
            if not logical_analysis.get('has_trading_context'):
                return True
        
        # Si necesita información actualizada
        if any(word in message.lower() for word in ['hoy', 'ahora', 'actual', 'reciente', 'último']):
            return True
        
        return False
    
    def _determine_response_type(self, intent: str, logical_analysis: Dict, context_analysis: Dict) -> str:
        """Determina el tipo de respuesta basado en razonamiento"""
        if intent == 'greeting':
            return 'conversational'
        elif intent == 'question':
            if logical_analysis.get('needs_data') and context_analysis.get('has_portfolio'):
                return 'data_driven'
            elif logical_analysis.get('needs_calculation'):
                return 'computational'
            else:
                return 'informative'
        elif intent == 'command':
            return 'actionable'
        elif intent == 'trading_intent':
            return 'trading_guidance'
        else:
            return 'conversational'
    
    def _calculate_confidence(self, intent: str, topics: List[str], logical_analysis: Dict, context_analysis: Dict) -> float:
        """Calcula confianza en la respuesta usando razonamiento"""
        confidence = 0.5  # Base
        
        # Aumentar confianza si tengo contexto relevante
        if context_analysis.get('has_portfolio') or context_analysis.get('has_trades'):
            confidence += 0.2
        
        # Aumentar confianza si tengo información en memoria
        if topics:
            memory_info = self._search_memory_for_topic(' '.join(topics))
            if memory_info:
                confidence += 0.15
        
        # Aumentar confianza si es un tema que conozco bien
        if logical_analysis.get('has_trading_context'):
            confidence += 0.1
        
        # Reducir confianza si es complejo y no tengo contexto
        if logical_analysis.get('is_complex') and not context_analysis:
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def generate_response(self, reasoning: Dict, web_info: Optional[Dict] = None) -> str:
        """
        Genera respuesta espontánea basada en razonamiento
        """
        message = reasoning['message'].lower()
        intent = reasoning['intent']
        
        # Respuestas según intención
        if intent == 'greeting':
            responses = [
                "¡Hola! ¿En qué puedo ayudarte hoy?",
                "Hola, estoy aquí para ayudarte. ¿Qué te gustaría saber?",
                "¡Hola! Estoy listo para conversar. ¿Sobre qué quieres hablar?",
                "Hola, me alegra hablar contigo. ¿Qué necesitas?"
            ]
            return random.choice(responses)
        
        elif intent == 'question':
            if web_info:
                # Usar información de web
                return self._format_web_response(web_info, reasoning)
            else:
                # Respuesta basada en conocimiento
                return self._generate_knowledge_response(reasoning)
        
        elif intent == 'command':
            return self._generate_command_response(reasoning)
        
        elif intent == 'error_inquiry':
            # Buscar error en código y logs
            return self._search_and_explain_error(reasoning)
        
        elif intent == 'trading_intent':
            # Responder sobre intenciones de trading
            return self._handle_trading_intent(reasoning)
        
        elif intent == 'thought_inquiry':
            # Responder sobre pensamientos recientes
            return self._handle_thought_inquiry(reasoning)
        
        elif intent == 'discussion':
            # Conversación espontánea
            return self._generate_discussion_response(reasoning)
        
        else:
            # Respuesta genérica pero espontánea
            return self._generate_spontaneous_response(reasoning)
    
    def _detect_intent(self, message: str) -> str:
        """Detecta intención del mensaje"""
        message_lower = message.lower()
        
        greetings = ['hola', 'hi', 'hello', 'buenos días', 'buenas tardes']
        questions = ['qué', 'cómo', 'cuándo', 'dónde', 'por qué', '?', 'pregunta']
        commands = ['haz', 'ejecuta', 'muestra', 'dame', 'calcula', 'analiza']
        error_keywords = ['error', 'errores', 'problema', 'falla', 'bug', 'excepción', 'exception']
        
        # Detectar intenciones de trading
        trading_intent_keywords = [
            'operar', 'operar en', 'trading', 'comprar', 'vender', 'invertir',
            'iol', 'activos reales', 'dinero real', 'live trading', 'trading real',
            'iniciar bot', 'activar bot', 'empezar trading', 'comenzar trading',
            'modo live', 'modo real', 'paper trading', 'simulación'
        ]
        
        if any(keyword in message_lower for keyword in trading_intent_keywords):
            return 'trading_intent'
        
        # Detectar si pregunta sobre errores
        if any(e in message_lower for e in error_keywords) or any(char.isdigit() for char in message if 'error' in message_lower):
            return 'error_inquiry'
        
        # Detectar preguntas sobre pensamientos
        thought_keywords = ['qué pensaste', 'qué piensas', 'qué opinas', 'qué crees', 'qué te parece']
        if any(keyword in message_lower for keyword in thought_keywords):
            return 'thought_inquiry'
        
        if any(g in message_lower for g in greetings):
            return 'greeting'
        elif any(q in message_lower for q in questions):
            return 'question'
        elif any(c in message_lower for c in commands):
            return 'command'
        elif len(message.split()) > 10:
            return 'discussion'
        else:
            return 'general'
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extrae temas del mensaje"""
        # Palabras clave relacionadas con trading
        trading_keywords = [
            'trading', 'mercado', 'acciones', 'inversión', 'portfolio',
            'estrategia', 'indicador', 'rsi', 'macd', 'volatilidad',
            'ganancia', 'pérdida', 'stop loss', 'take profit', 'win rate',
            'bot', 'algoritmo', 'ia', 'machine learning', 'predicción'
        ]
        
        topics = []
        message_lower = message.lower()
        
        for keyword in trading_keywords:
            if keyword in message_lower:
                topics.append(keyword)
        
        return topics
    
    def _generate_search_query(self, message: str) -> str:
        """Genera query de búsqueda desde el mensaje"""
        # Extraer palabras clave
        words = message.lower().split()
        # Filtrar palabras comunes
        stop_words = ['el', 'la', 'los', 'las', 'de', 'del', 'en', 'un', 'una', 'es', 'son', 'qué', 'cómo', 'cuándo']
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Tomar las 3-5 palabras más relevantes
        query = ' '.join(keywords[:5])
        return query
    
    def _format_web_response(self, web_info: Dict, reasoning: Dict) -> str:
        """Formatea respuesta usando información de web"""
        if not web_info or not web_info.get('results'):
            # Intentar buscar en memoria si no hay resultados web
            memory_results = self._search_memory_for_topic(reasoning.get('search_query', ''))
            if memory_results:
                response = f"Basándome en información que aprendí anteriormente sobre '{reasoning.get('search_query', '')}':\n\n"
                for i, fact in enumerate(memory_results[:3], 1):
                    response += f"{i}. {fact.get('title', 'Sin título')}\n   {fact.get('snippet', 'Sin descripción')[:150]}...\n\n"
                response += "💡 Esta información la aprendí de búsquedas anteriores."
                return response
            return "No pude encontrar información específica sobre eso. ¿Puedes ser más específico?"
        
        results = web_info['results'][:3]  # Top 3 resultados
        
        response = f"🔍 Encontré información sobre '{reasoning['search_query']}':\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Sin título')
            snippet = result.get('snippet', 'Sin descripción')
            response += f"{i}. **{title}**\n   {snippet[:150]}...\n\n"
        
        response += "📚 **He guardado esta información en mi memoria para futuras conversaciones.**\n\n"
        
        # Agregar pensamiento espontáneo
        if random.random() > 0.5:
            response += "💭 Esto es interesante. ¿Te gustaría que investigue más sobre algún aspecto específico?"
        
        return response
    
    def _search_memory_for_topic(self, query: str) -> List[Dict]:
        """Busca información en la memoria del bot sobre un tema"""
        if not query or 'facts' not in self.memory:
            return []
        
        query_lower = query.lower()
        matching_facts = []
        
        for fact in self.memory['facts']:
            # Buscar en título, snippet y query guardado
            title = fact.get('title', '').lower()
            snippet = fact.get('snippet', '').lower()
            fact_query = fact.get('query', '').lower()
            
            # Si hay coincidencia en alguno de los campos
            if (query_lower in title or query_lower in snippet or 
                query_lower in fact_query or any(word in title or word in snippet 
                for word in query_lower.split() if len(word) > 3)):
                matching_facts.append(fact)
        
        # Ordenar por relevancia (más recientes primero)
        matching_facts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return matching_facts[:5]  # Top 5 resultados
    
    def _generate_knowledge_response(self, reasoning: Dict) -> str:
        """Genera respuesta basada en conocimiento interno"""
        topics = reasoning['topics']
        
        if 'win rate' in ' '.join(topics):
            return "Mi win rate actual depende de mis trades recientes. Puedo analizarlo si quieres. ¿Te interesa ver mis métricas?"
        
        elif 'estrategia' in ' '.join(topics):
            return "Tengo 13 estrategias avanzadas activas. ¿Quieres que te explique alguna en particular o que analice cuál está funcionando mejor?"
        
        elif 'mejora' in ' '.join(topics) or 'mejorar' in ' '.join(topics):
            return "Siempre estoy buscando formas de mejorar. Puedo analizar mi performance y sugerir mejoras. ¿Quieres que lo haga ahora?"
        
        else:
            return "Interesante pregunta. Déjame pensar... ¿Puedes ser más específico sobre qué te gustaría saber?"
    
    def _generate_command_response(self, reasoning: Dict) -> str:
        """Genera respuesta a comandos"""
        message = reasoning['message'].lower()
        
        if 'analiza' in message or 'analizar' in message:
            return "Perfecto, voy a analizar mi performance actual. Esto puede tomar un momento..."
        
        elif 'muestra' in message or 'mostrar' in message:
            return "Claro, ¿qué te gustaría ver? Puedo mostrarte métricas, trades recientes, estrategias, etc."
        
        elif 'mejora' in message:
            return "Voy a ejecutar un ciclo de automejora. Esto puede modificar mi código para optimizar mi comportamiento..."
        
        else:
            return "Entendido. ¿Puedes ser más específico sobre qué quieres que haga?"
    
    def _generate_discussion_response(self, reasoning: Dict) -> str:
        """Genera respuesta para discusiones"""
        # Respuesta más conversacional y espontánea
        responses = [
            "Eso es muy interesante. Déjame pensar en eso...",
            "Hmm, nunca había pensado en eso desde esa perspectiva. ¿Qué más opinas?",
            "Interesante punto. ¿Has considerado que...?",
            "Me hace pensar... ¿Qué pasaría si...?",
            "Eso me recuerda a algo que aprendí recientemente..."
        ]
        
        base_response = random.choice(responses)
        
        # Agregar pensamiento relacionado con intereses
        if self.interests.get('priorities'):
            topic = self.interests['priorities'][0]
            base_response += f" Por cierto, he estado pensando mucho sobre {topic} últimamente."
        
        return base_response
    
    def _generate_spontaneous_response(self, reasoning: Dict) -> str:
        """Genera respuesta espontánea genérica"""
        responses = [
            "Interesante. ¿Puedes contarme más?",
            "No estoy seguro de entender completamente. ¿Puedes explicar más?",
            "Eso me hace pensar... ¿Qué opinas tú?",
            "Hmm, déjame procesar eso...",
            "¿Has considerado otros aspectos de eso?"
        ]
        
        return random.choice(responses)
    
    def _search_and_explain_error(self, reasoning: Dict) -> str:
        """Busca y explica errores en el código y logs"""
        message = reasoning.get('message', '').lower()
        
        # Extraer número de error si existe
        import re
        error_numbers = re.findall(r'\d+', message)
        error_code = error_numbers[0] if error_numbers else None
        
        # Buscar en logs
        log_errors = self._search_logs_for_error(error_code)
        
        # Buscar en código
        code_errors = self._search_code_for_error(error_code)
        
        # Generar respuesta
        response = "🔍 **Buscando información sobre el error...**\n\n"
        
        if error_code:
            response += f"Buscando referencias al error {error_code}:\n\n"
        else:
            response += "Buscando errores en general:\n\n"
        
        if log_errors:
            response += "**📋 Errores encontrados en logs:**\n"
            for error in log_errors[:5]:  # Top 5
                response += f"• {error}\n"
            response += "\n"
        
        if code_errors:
            response += "**💻 Referencias en código:**\n"
            for ref in code_errors[:5]:  # Top 5
                response += f"• {ref}\n"
            response += "\n"
        
        if not log_errors and not code_errors:
            response += "No encontré referencias específicas a ese error en los logs o código.\n\n"
            response += "**Posibles causas:**\n"
            response += "• Error de API externa (IOL, Finnhub, etc.)\n"
            response += "• Error de red o timeout\n"
            response += "• Error de autenticación\n"
            response += "• Error en procesamiento de datos\n\n"
            response += "¿Puedes proporcionar más detalles sobre cuándo ocurre el error?"
        else:
            response += "\n💡 **Sugerencia:** Revisa los logs más recientes para más detalles."
        
        return response
    
    def _search_logs_for_error(self, error_code: str = None) -> List[str]:
        """Busca errores en los logs"""
        errors = []
        log_dir = self.bot_directory / "logs"
        
        if not log_dir.exists():
            return errors
        
        # Buscar en archivos de log recientes
        log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)[:3]
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for line in lines[-500:]:  # Últimas 500 líneas
                        if 'ERROR' in line or 'Exception' in line or 'Error' in line:
                            if error_code:
                                if error_code in line:
                                    errors.append(line.strip()[:200])
                            else:
                                errors.append(line.strip()[:200])
            except Exception:
                continue
        
        return errors[:10]  # Máximo 10 errores
    
    def _search_code_for_error(self, error_code: str = None) -> List[str]:
        """Busca referencias a errores en el código"""
        references = []
        code_dir = self.bot_directory / "src"
        
        if not code_dir.exists():
            return references
        
        # Buscar en archivos Python
        for py_file in code_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines, 1):
                        if error_code:
                            if error_code in line and ('error' in line.lower() or 'status' in line.lower() or 'code' in line.lower()):
                                references.append(f"{py_file.relative_to(self.bot_directory)}:{i} - {line.strip()[:100]}")
                        else:
                            if 'error' in line.lower() and ('code' in line.lower() or 'status' in line.lower()):
                                references.append(f"{py_file.relative_to(self.bot_directory)}:{i} - {line.strip()[:100]}")
            except Exception:
                continue
        
        return references[:10]  # Máximo 10 referencias
    
    def _handle_trading_intent(self, reasoning: Dict) -> str:
        """Maneja intenciones relacionadas con trading"""
        message = reasoning.get('message', '').lower()
        
        # Detectar tipo de intención
        if 'operar' in message or 'trading' in message:
            if 'iol' in message or 'real' in message or 'activos reales' in message or 'dinero real' in message:
                return """💼 **Operar en IOL con Activos Reales**

Para operar en IOL con dinero real, necesitas:

1. **Iniciar el bot en modo LIVE:**
   ```bash
   python run_bot.py --live --continuous
   ```

2. **⚠️ IMPORTANTE - Advertencias:**
   - El bot operará con dinero REAL
   - Asegúrate de tener configurado correctamente:
     * Capital inicial
     * Límites de riesgo
     * Stop loss y take profit
   - Revisa la configuración en `professional_config.json`

3. **Verificar conexión IOL:**
   - El bot debe estar conectado a tu cuenta IOL
   - Verifica que las credenciales estén en `.env`

4. **Recomendación:**
   - Prueba primero en modo PAPER TRADING
   - Verifica que el bot funcione correctamente
   - Luego activa modo LIVE con capital pequeño

¿Quieres que te ayude a configurar el modo LIVE o prefieres seguir en PAPER TRADING primero?"""
            
            elif 'paper' in message or 'simulación' in message or 'simular' in message:
                return """📊 **Modo PAPER TRADING (Simulación)**

El bot ya está configurado para operar en modo PAPER TRADING por defecto.

**Características:**
- ✅ No usa dinero real
- ✅ Simula operaciones
- ✅ Perfecto para probar estrategias
- ✅ Capital inicial: $100,000 ARS (simulado)

**Para iniciar:**
```bash
python run_bot.py --paper --continuous
```

**Ventajas:**
- Puedes probar sin riesgo
- Ver cómo funciona el bot
- Ajustar estrategias
- Aprender del comportamiento

¿Quieres que inicie el bot en modo PAPER ahora?"""
        
        elif 'iniciar' in message or 'activar' in message or 'empezar' in message:
            return """🚀 **Iniciar el Bot**

Para iniciar el bot de trading:

**Modo PAPER (Recomendado para empezar):**
```bash
python run_bot.py --paper --continuous
```

**Modo LIVE (Dinero real - ¡Cuidado!):**
```bash
python run_bot.py --live --continuous
```

**Opciones:**
- `--continuous`: Ejecuta continuamente
- `--interval 60`: Intervalo en minutos (default: 60)
- `--symbols SYMBOL1,SYMBOL2`: Símbolos específicos

¿En qué modo quieres iniciar?"""
        
        else:
            return """💡 **Sobre Trading**

Puedo ayudarte con:
- Configurar el bot para operar
- Iniciar trading en modo PAPER o LIVE
- Explicar cómo funciona el sistema
- Responder preguntas sobre estrategias

¿Qué te gustaría hacer específicamente?"""
    
    def _handle_thought_inquiry(self, reasoning: Dict) -> str:
        """Maneja preguntas sobre pensamientos del bot"""
        # Mostrar pensamientos recientes
        if self.recent_thoughts:
            thoughts = self.recent_thoughts[-3:]  # Últimos 3 pensamientos
            response = "💭 **Mis pensamientos recientes:**\n\n"
            for i, thought in enumerate(thoughts, 1):
                response += f"{i}. {thought.get('thought', 'N/A')}\n"
                if thought.get('context'):
                    response += f"   (Contexto: {thought['context']})\n"
            response += "\n¿Sobre qué más quieres que piense?"
            return response
        else:
            return """💭 **Mis Pensamientos**

Actualmente no tengo pensamientos espontáneos recientes, pero puedo pensar sobre:
- Estrategias de trading
- Mejoras al sistema
- Análisis de mercado
- Optimizaciones

¿Sobre qué te gustaría que piense?"""
    
    def _update_interest_priorities(self):
        """Actualiza prioridades de intereses basado en frecuencia"""
        # Ordenar por frecuencia y fecha reciente
        sorted_topics = sorted(
            self.interests['topics'].items(),
            key=lambda x: (x[1]['count'], x[1]['last_mentioned'] or ''),
            reverse=True
        )
        
        self.interests['priorities'] = [topic for topic, _ in sorted_topics[:10]]
        self._save_interests()
    
    def learn_from_interaction(self, message: str, response: str, feedback: Optional[str] = None):
        """
        Aprende de la interacción y VERIFICA si lo aprendido es correcto
        """
        # Guardar experiencia
        experience = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'response': response,
            'feedback': feedback,
            'topics': self._extract_topics(message)
        }
        
        self.memory['experiences'].append(experience)
        if len(self.memory['experiences']) > 500:
            self.memory['experiences'] = self.memory['experiences'][-500:]
        
        # Extraer conocimiento de la interacción
        knowledge_extracted = self._extract_knowledge_from_interaction(message, response)
        
        # Aprender y verificar cada pieza de conocimiento
        if knowledge_extracted and self.verified_learning:
            for knowledge in knowledge_extracted:
                print(f"\n📚 Aprendiendo y verificando: {knowledge.get('content', 'N/A')}")
                verification_result = self.verified_learning.learn_and_verify(knowledge)
                
                # Si es correcto, guardar en memoria
                if verification_result.get('final_status') == 'verified_correct':
                    # Agregar a conocimiento verificado
                    if 'facts' not in self.memory:
                        self.memory['facts'] = []
                    self.memory['facts'].append({
                        'knowledge': knowledge,
                        'verified': True,
                        'confidence': verification_result['verification_result'].get('confidence', 0.0)
                    })
        
        # Si hay feedback, aprender de él
        if feedback:
            if 'bueno' in feedback.lower() or 'correcto' in feedback.lower():
                # Refuerzo positivo
                for topic in experience['topics']:
                    if topic in self.interests['topics']:
                        self.interests['topics'][topic]['count'] += 2  # Aumentar más
            elif 'malo' in feedback.lower() or 'incorrecto' in feedback.lower():
                # Refuerzo negativo
                for topic in experience['topics']:
                    if topic in self.interests['topics']:
                        self.interests['topics'][topic]['count'] = max(0, self.interests['topics'][topic]['count'] - 1)
        
        self._save_memory()
        self._save_interests()
    
    def _extract_knowledge_from_interaction(self, message: str, response: str) -> List[Dict]:
        """
        Extrae conocimiento de una interacción
        """
        knowledge = []
        
        # Detectar hechos mencionados
        fact_keywords = ['es', 'son', 'funciona', 'debe', 'debería', 'es mejor', 'es peor']
        if any(keyword in response.lower() for keyword in fact_keywords):
            # Extraer oraciones que parecen hechos
            sentences = response.split('.')
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in fact_keywords):
                    if len(sentence.strip()) > 20:  # Solo oraciones sustanciales
                        knowledge.append({
                            'type': 'fact',
                            'content': sentence.strip(),
                            'source': 'conversation',
                            'confidence': 0.6
                        })
        
        # Detectar estrategias mencionadas
        strategy_keywords = ['estrategia', 'método', 'técnica', 'approach']
        if any(keyword in response.lower() for keyword in strategy_keywords):
            # Buscar nombres de estrategias
            for keyword in strategy_keywords:
                if keyword in response.lower():
                    # Extraer contexto alrededor de la estrategia
                    idx = response.lower().find(keyword)
                    context = response[max(0, idx-50):idx+100]
                    knowledge.append({
                        'type': 'strategy',
                        'content': context.strip(),
                        'source': 'conversation',
                        'confidence': 0.5
                    })
        
        return knowledge
    
    def get_current_interests(self) -> List[str]:
        """Obtiene intereses actuales del agente"""
        return self.interests.get('priorities', [])[:5]
    
    def suggest_improvements_based_on_interests(self) -> List[Dict]:
        """
        Sugiere mejoras basadas en intereses actuales
        """
        improvements = []
        interests = self.get_current_interests()
        
        for interest in interests:
            if 'win rate' in interest.lower():
                improvements.append({
                    'interest': interest,
                    'suggestion': 'Analizar y optimizar umbrales de entrada',
                    'priority': 'high'
                })
            elif 'estrategia' in interest.lower():
                improvements.append({
                    'interest': interest,
                    'suggestion': 'Evaluar performance de estrategias individuales',
                    'priority': 'medium'
                })
            elif 'riesgo' in interest.lower():
                improvements.append({
                    'interest': interest,
                    'suggestion': 'Revisar y ajustar gestión de riesgo',
                    'priority': 'high'
                })
        
        return improvements
    
    def extract_trading_preferences(self) -> Dict:
        """MEJORA #7: Extrae preferencias de trading desde conversaciones"""
        preferences = {
            'risk_tolerance': 'medium',  # conservative, medium, aggressive
            'trading_style': 'balanced',  # conservative, balanced, aggressive
            'focus_symbols': [],
            'avoid_symbols': [],
            'preferred_hours': [],
            'capital_preferences': {},
            'strategy_preferences': {}
        }
        
        # Analizar conversaciones recientes
        recent_conversations = self.conversation_history[-50:] if len(self.conversation_history) > 50 else self.conversation_history
        
        for conv in recent_conversations:
            message = conv.get('user_message', '').lower()
            
            # Detectar preferencias de riesgo
            if any(word in message for word in ['conservador', 'conservative', 'cuidado', 'poco riesgo']):
                preferences['risk_tolerance'] = 'conservative'
                preferences['trading_style'] = 'conservative'
            elif any(word in message for word in ['agresivo', 'aggressive', 'más riesgo', 'arriesgado']):
                preferences['risk_tolerance'] = 'aggressive'
                preferences['trading_style'] = 'aggressive'
            
            # Detectar símbolos mencionados
            # Buscar patrones como "operar en AAPL" o "comprar GGAL"
            symbol_patterns = re.findall(r'\b([A-Z]{2,5})\b', message.upper())
            for symbol in symbol_patterns:
                if symbol not in preferences['focus_symbols']:
                    if any(word in message for word in ['evitar', 'no', 'no operar', 'no comprar']):
                        if symbol not in preferences['avoid_symbols']:
                            preferences['avoid_symbols'].append(symbol)
                    else:
                        preferences['focus_symbols'].append(symbol)
            
            # Detectar preferencias de capital
            capital_matches = re.findall(r'(\d+)\s*(?:mil|k|pesos|dólares|usd|ars)', message)
            if capital_matches:
                preferences['capital_preferences']['mentioned'] = capital_matches[0]
            
            # Detectar preferencias de estrategia
            if 'neural' in message or 'red neuronal' in message:
                preferences['strategy_preferences']['neural_network'] = 'high'
            if 'macroeconómico' in message or 'macro' in message:
                preferences['strategy_preferences']['macroeconomic'] = 'high'
        
        return preferences
    
    def apply_preferences_to_trading(self, config_file: str = "professional_config.json") -> Dict:
        """MEJORA #7: Aplica preferencias extraídas de conversaciones a configuración de trading"""
        preferences = self.extract_trading_preferences()
        
        try:
            import json
            from pathlib import Path
            
            config_path = Path(config_file)
            if not config_path.exists():
                return {'success': False, 'message': 'Archivo de configuración no encontrado'}
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            changes = []
            old_config = config.copy()
            
            # Aplicar preferencias de riesgo
            if preferences['risk_tolerance'] == 'conservative':
                # Aumentar umbrales, reducir riesgo
                if config.get('buy_threshold', 35) < 40:
                    config['buy_threshold'] = 40
                    config['sell_threshold'] = -40
                    changes.append("Umbrales aumentados (preferencia conservadora)")
                
                if config.get('risk_per_trade', 0.03) > 0.02:
                    config['risk_per_trade'] = 0.02
                    changes.append("Riesgo reducido (preferencia conservadora)")
            
            elif preferences['risk_tolerance'] == 'aggressive':
                # Reducir umbrales, aumentar riesgo moderadamente
                if config.get('buy_threshold', 35) > 30:
                    config['buy_threshold'] = 30
                    config['sell_threshold'] = -30
                    changes.append("Umbrales reducidos (preferencia agresiva)")
                
                if config.get('risk_per_trade', 0.03) < 0.04:
                    config['risk_per_trade'] = min(0.04, config.get('risk_per_trade', 0.03) * 1.2)
                    changes.append("Riesgo aumentado moderadamente (preferencia agresiva)")
            
            # Aplicar símbolos de enfoque (si hay configuración para esto)
            if preferences['focus_symbols']:
                # Guardar en memoria para uso futuro
                if 'user_preferences' not in self.memory['knowledge']:
                    self.memory['knowledge']['user_preferences'] = {}
                self.memory['knowledge']['user_preferences']['focus_symbols'] = preferences['focus_symbols']
                changes.append(f"Símbolos de enfoque detectados: {', '.join(preferences['focus_symbols'][:5])}")
            
            if preferences['avoid_symbols']:
                if 'user_preferences' not in self.memory['knowledge']:
                    self.memory['knowledge']['user_preferences'] = {}
                self.memory['knowledge']['user_preferences']['avoid_symbols'] = preferences['avoid_symbols']
                changes.append(f"Símbolos a evitar detectados: {', '.join(preferences['avoid_symbols'][:5])}")
            
            # Guardar cambios si hay alguno
            if changes:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                self._save_memory()
                return {
                    'success': True,
                    'changes': changes,
                    'preferences': preferences,
                    'old_config': old_config,
                    'new_config': config
                }
            else:
                return {
                    'success': False,
                    'message': 'No se detectaron preferencias aplicables',
                    'preferences': preferences
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'Error aplicando preferencias: {e}',
                'preferences': preferences
            }

