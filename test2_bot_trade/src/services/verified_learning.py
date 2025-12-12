"""
Verified Learning - Sistema de aprendizaje con verificación
El bot aprende y luego verifica si lo aprendido es correcto
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from src.services.web_search_agent import WebSearchAgent


class VerifiedLearning:
    """
    Sistema que aprende y verifica la corrección del conocimiento
    """
    
    def __init__(self, bot_directory: str = "."):
        self.bot_directory = Path(bot_directory)
        self.verified_knowledge_file = self.bot_directory / "data" / "verified_knowledge.json"
        self.pending_verification_file = self.bot_directory / "data" / "pending_verification.json"
        
        self.verified_knowledge = self._load_verified_knowledge()
        self.pending_verification = self._load_pending_verification()
        
        self.web_search = WebSearchAgent()
        
        # Estadísticas
        self.verification_stats = {
            'total_learned': 0,
            'verified_correct': 0,
            'verified_incorrect': 0,
            'pending': 0
        }
    
    def _load_verified_knowledge(self) -> Dict:
        """Carga conocimiento verificado"""
        if self.verified_knowledge_file.exists():
            try:
                with open(self.verified_knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
                    return {'facts': [], 'strategies': [], 'patterns': []}
            except:
                return {'facts': [], 'strategies': [], 'patterns': []}
        return {'facts': [], 'strategies': [], 'patterns': []}
    
    def _save_verified_knowledge(self):
        """Guarda conocimiento verificado"""
        self.verified_knowledge_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.verified_knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(self.verified_knowledge, f, indent=2, ensure_ascii=False)
    
    def _load_pending_verification(self) -> List[Dict]:
        """Carga conocimiento pendiente de verificación"""
        if self.pending_verification_file.exists():
            try:
                with open(self.pending_verification_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_pending_verification(self):
        """Guarda conocimiento pendiente de verificación"""
        self.pending_verification_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.pending_verification_file, 'w', encoding='utf-8') as f:
            json.dump(self.pending_verification, f, indent=2, ensure_ascii=False)
    
    def learn_and_verify(self, knowledge: Dict) -> Dict:
        """
        Aprende algo nuevo y luego lo verifica
        
        Args:
            knowledge: Diccionario con el conocimiento a aprender
                {
                    'type': 'fact' | 'strategy' | 'pattern',
                    'content': 'Descripción del conocimiento',
                    'source': 'De dónde viene',
                    'confidence': 0.0-1.0
                }
        
        Returns:
            Dict con resultado de verificación
        """
        print(f"\n📚 Aprendiendo: {knowledge.get('content', 'N/A')}")
        
        # 1. Aprender (guardar temporalmente)
        learning_record = {
            'timestamp': datetime.now().isoformat(),
            'knowledge': knowledge,
            'status': 'pending_verification',
            'verification_attempts': 0
        }
        
        self.pending_verification.append(learning_record)
        self._save_pending_verification()
        self.verification_stats['total_learned'] += 1
        self.verification_stats['pending'] += 1
        
        # 2. Verificar inmediatamente
        verification_result = self.verify_knowledge(knowledge)
        
        # 3. Procesar resultado
        if verification_result['is_correct']:
            # Conocimiento correcto - guardar en conocimiento verificado
            self._add_verified_knowledge(knowledge, verification_result)
            learning_record['status'] = 'verified_correct'
            self.verification_stats['verified_correct'] += 1
            self.verification_stats['pending'] -= 1
            print(f"   ✅ Verificado como CORRECTO")
        else:
            # Conocimiento incorrecto - marcar y corregir
            learning_record['status'] = 'verified_incorrect'
            learning_record['correction'] = verification_result.get('correction')
            self.verification_stats['verified_incorrect'] += 1
            self.verification_stats['pending'] -= 1
            print(f"   ❌ Verificado como INCORRECTO")
            print(f"   💡 Corrección: {verification_result.get('correction', 'N/A')}")
            
            # Aprender la versión corregida
            if verification_result.get('corrected_knowledge'):
                corrected = verification_result['corrected_knowledge']
                print(f"   🔄 Aprendiendo versión corregida...")
                return self.learn_and_verify(corrected)  # Verificar la corrección también
        
        # Actualizar registro
        learning_record['verification_result'] = verification_result
        learning_record['verified_at'] = datetime.now().isoformat()
        
        # Mover de pending a verified (o descartar si incorrecto)
        self.pending_verification = [p for p in self.pending_verification 
                                    if p.get('timestamp') != learning_record['timestamp']]
        self._save_pending_verification()
        
        return {
            'learning_record': learning_record,
            'verification_result': verification_result,
            'final_status': learning_record['status']
        }
    
    def verify_knowledge(self, knowledge: Dict) -> Dict:
        """
        Verifica si un conocimiento es correcto buscando información
        
        Args:
            knowledge: Conocimiento a verificar
        
        Returns:
            Dict con resultado de verificación
        """
        knowledge_type = knowledge.get('type', 'fact')
        content = knowledge.get('content', '')
        
        print(f"   🔍 Verificando conocimiento...")
        
        # Generar query de búsqueda para verificar
        verification_query = self._generate_verification_query(knowledge)
        
        # Buscar información
        search_results = self.web_search.search(verification_query, num_results=5)
        
        if search_results.get('error'):
            # Si hay error en búsqueda, no podemos verificar
            return {
                'is_correct': None,  # Desconocido
                'confidence': 0.0,
                'reason': 'No se pudo buscar información para verificar',
                'error': search_results['error']
            }
        
        # Analizar resultados
        verification_result = self._analyze_verification_results(
            knowledge, search_results
        )
        
        return verification_result
    
    def _generate_verification_query(self, knowledge: Dict) -> str:
        """Genera query de búsqueda para verificar conocimiento"""
        content = knowledge.get('content', '')
        knowledge_type = knowledge.get('type', 'fact')
        
        # Extraer palabras clave
        if knowledge_type == 'strategy':
            # Para estrategias, buscar si la estrategia es válida
            query = f"estrategia trading {content} es correcta válida"
        elif knowledge_type == 'pattern':
            # Para patrones, buscar si el patrón es reconocido
            query = f"patrón trading {content} reconocido válido"
        else:
            # Para hechos, buscar información general
            query = f"{content} trading correcto verdadero"
        
        return query
    
    def _analyze_verification_results(self, knowledge: Dict, search_results: Dict) -> Dict:
        """
        Analiza resultados de búsqueda para determinar si el conocimiento es correcto
        """
        results = search_results.get('results', [])
        
        if not results:
            return {
                'is_correct': None,
                'confidence': 0.0,
                'reason': 'No se encontraron resultados para verificar'
            }
        
        # Analizar snippets de resultados
        content = knowledge.get('content', '').lower()
        positive_indicators = 0
        negative_indicators = 0
        neutral_indicators = 0
        
        # Palabras clave que indican corrección
        positive_keywords = [
            'correcto', 'válido', 'verdadero', 'confirmado', 'reconocido',
            'efectivo', 'funciona', 'probado', 'establecido', 'aceptado',
            'correct', 'valid', 'true', 'confirmed', 'recognized',
            'effective', 'works', 'proven', 'established'
        ]
        
        # Palabras clave que indican incorrección
        negative_keywords = [
            'incorrecto', 'falso', 'erróneo', 'inválido', 'desmentido',
            'no funciona', 'inefectivo', 'rechazado', 'descartado',
            'incorrect', 'false', 'wrong', 'invalid', 'debunked',
            "doesn't work", 'ineffective', 'rejected', 'discarded'
        ]
        
        # Analizar cada resultado
        for result in results:
            snippet = result.get('snippet', '').lower()
            title = result.get('title', '').lower()
            text = f"{title} {snippet}"
            
            # Contar indicadores
            for keyword in positive_keywords:
                if keyword in text:
                    positive_indicators += 1
            
            for keyword in negative_keywords:
                if keyword in text:
                    negative_indicators += 1
            
            # Verificar si el contenido específico aparece
            if any(word in text for word in content.split()[:3]):  # Primeras 3 palabras
                if any(kw in text for kw in positive_keywords):
                    positive_indicators += 2  # Más peso si menciona el contenido
                elif any(kw in text for kw in negative_keywords):
                    negative_indicators += 2
        
        # Determinar si es correcto
        total_indicators = positive_indicators + negative_indicators
        
        if total_indicators == 0:
            return {
                'is_correct': None,
                'confidence': 0.0,
                'reason': 'No se encontraron indicadores claros',
                'positive_indicators': 0,
                'negative_indicators': 0
            }
        
        # Calcular confianza
        confidence = abs(positive_indicators - negative_indicators) / total_indicators
        
        # Decisión
        if positive_indicators > negative_indicators * 1.5:  # 50% más positivo
            is_correct = True
            reason = f"Encontrados {positive_indicators} indicadores positivos vs {negative_indicators} negativos"
        elif negative_indicators > positive_indicators * 1.5:  # 50% más negativo
            is_correct = False
            reason = f"Encontrados {negative_indicators} indicadores negativos vs {positive_indicators} positivos"
            # Intentar encontrar corrección
            correction = self._find_correction(knowledge, search_results)
        else:
            is_correct = None  # Inconcluso
            reason = f"Indicadores balanceados: {positive_indicators} positivos, {negative_indicators} negativos"
            correction = None
        
        result = {
            'is_correct': is_correct,
            'confidence': confidence,
            'reason': reason,
            'positive_indicators': positive_indicators,
            'negative_indicators': negative_indicators,
            'sources_checked': len(results)
        }
        
        if is_correct is False and correction:
            result['correction'] = correction
            result['corrected_knowledge'] = {
                'type': knowledge.get('type'),
                'content': correction,
                'source': 'verified_learning_correction',
                'confidence': 0.7
            }
        
        return result
    
    def _find_correction(self, knowledge: Dict, search_results: Dict) -> Optional[str]:
        """Intenta encontrar la versión correcta del conocimiento"""
        results = search_results.get('results', [])
        
        # Buscar información alternativa en los resultados
        for result in results:
            snippet = result.get('snippet', '')
            # Extraer información relevante del snippet
            # (Implementación simplificada - se puede mejorar)
            if len(snippet) > 50:
                # Tomar las primeras palabras relevantes
                words = snippet.split()[:20]
                correction = ' '.join(words)
                return correction
        
        return None
    
    def _add_verified_knowledge(self, knowledge: Dict, verification: Dict):
        """Agrega conocimiento verificado"""
        knowledge_type = knowledge.get('type', 'fact')
        
        verified_item = {
            'knowledge': knowledge,
            'verification': verification,
            'verified_at': datetime.now().isoformat(),
            'confidence': verification.get('confidence', 0.0)
        }
        
        if knowledge_type == 'fact':
            self.verified_knowledge['facts'].append(verified_item)
        elif knowledge_type == 'strategy':
            self.verified_knowledge['strategies'].append(verified_item)
        elif knowledge_type == 'pattern':
            self.verified_knowledge['patterns'].append(verified_item)
        
        # Limitar tamaño
        for key in self.verified_knowledge:
            if len(self.verified_knowledge[key]) > 1000:
                self.verified_knowledge[key] = self.verified_knowledge[key][-1000:]
        
        self._save_verified_knowledge()
    
    def verify_pending_knowledge(self) -> Dict:
        """
        Verifica todo el conocimiento pendiente
        """
        print(f"\n🔍 Verificando {len(self.pending_verification)} elementos pendientes...")
        
        verified_count = 0
        incorrect_count = 0
        inconclusive_count = 0
        
        for item in self.pending_verification[:10]:  # Verificar hasta 10 a la vez
            knowledge = item.get('knowledge', {})
            verification = self.verify_knowledge(knowledge)
            
            if verification['is_correct'] is True:
                self._add_verified_knowledge(knowledge, verification)
                item['status'] = 'verified_correct'
                verified_count += 1
            elif verification['is_correct'] is False:
                item['status'] = 'verified_incorrect'
                item['correction'] = verification.get('correction')
                incorrect_count += 1
            else:
                item['status'] = 'inconclusive'
                inconclusive_count += 1
            
            item['verification_result'] = verification
            item['verified_at'] = datetime.now().isoformat()
        
        # Guardar
        self._save_pending_verification()
        self._save_verified_knowledge()
        
        return {
            'verified': verified_count,
            'incorrect': incorrect_count,
            'inconclusive': inconclusive_count,
            'total_checked': verified_count + incorrect_count + inconclusive_count
        }
    
    def get_verified_knowledge(self, knowledge_type: Optional[str] = None) -> List[Dict]:
        """Obtiene conocimiento verificado"""
        if knowledge_type:
            return self.verified_knowledge.get(knowledge_type, [])
        else:
            # Retornar todo
            all_knowledge = []
            for key in self.verified_knowledge:
                all_knowledge.extend(self.verified_knowledge[key])
            return all_knowledge
    
    def get_verification_stats(self) -> Dict:
        """Obtiene estadísticas de verificación"""
        return {
            **self.verification_stats,
            'verified_knowledge_count': sum(
                len(self.verified_knowledge[key]) 
                for key in self.verified_knowledge
            ),
            'pending_count': len(self.pending_verification)
        }

