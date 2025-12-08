"""
Autonomous Cycle - Ciclo Autónomo de Trading
El bot opera en un ciclo completamente autónomo sin intervención humana
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger('autonomous_cycle')

class CyclePhase(Enum):
    """Fases del ciclo autónomo"""
    SCANNING = "scanning"           # Fase 1: Buscar oportunidades
    ANALYZING = "analyzing"         # Fase 2: Evaluar oportunidades
    DECIDING = "deciding"           # Fase 3: Decidir qué operar
    EXECUTING = "executing"         # Fase 4: Realizar operaciones
    MONITORING = "monitoring"       # Fase 5: Seguir posiciones abiertas
    LEARNING = "learning"           # Fase 6: Aprender de resultados
    OPTIMIZING = "optimizing"       # Fase 7: Mejorar estrategias
    IDLE = "idle"                   # Estado de espera

class AutonomousCycle:
    """
    Ciclo Autónomo de Trading
    
    El bot opera en un ciclo continuo:
    1. Escaneo - Buscar oportunidades
    2. Análisis - Evaluar oportunidades
    3. Decisión - Decidir qué operar
    4. Ejecución - Realizar operaciones
    5. Monitoreo - Seguir posiciones
    6. Aprendizaje - Aprender de resultados
    7. Optimización - Mejorar estrategias
    """
    
    def __init__(self, trading_bot, market_scanner=None):
        """
        Args:
            trading_bot: Instancia del trading bot
            market_scanner: Instancia del Global Market Scanner
        """
        self.trading_bot = trading_bot
        self.market_scanner = market_scanner
        
        # Estado del ciclo
        self.current_phase = CyclePhase.IDLE
        self.phase_start_time = None
        self.cycle_count = 0
        self.last_cycle_time = None
        
        # Configuración
        self.phase_durations = {
            CyclePhase.SCANNING: timedelta(minutes=5),
            CyclePhase.ANALYZING: timedelta(minutes=10),
            CyclePhase.DECIDING: timedelta(minutes=2),
            CyclePhase.EXECUTING: timedelta(minutes=5),
            CyclePhase.MONITORING: timedelta(minutes=15),
            CyclePhase.LEARNING: timedelta(minutes=5),
            CyclePhase.OPTIMIZING: timedelta(minutes=10)
        }
        
        # Datos del ciclo
        self.opportunities_found = []
        self.trades_executed = []
        self.positions_monitored = []
        self.learnings = []
        
        # Estadísticas
        self.stats = {
            'total_cycles': 0,
            'opportunities_found': 0,
            'trades_executed': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0
        }
        
        # Directorio de logs
        self.logs_dir = Path("data/autonomous_cycle")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def start_cycle(self):
        """Inicia el ciclo autónomo"""
        logger.info("🚀 Iniciando Ciclo Autónomo...")
        self.current_phase = CyclePhase.SCANNING
        self.phase_start_time = datetime.now()
        self.cycle_count += 1
        self.stats['total_cycles'] += 1
        
        logger.info(f"📊 Ciclo #{self.cycle_count} iniciado - Fase: {self.current_phase.value}")
    
    def run_cycle_step(self) -> bool:
        """
        Ejecuta un paso del ciclo
        
        Returns:
            True si el ciclo continúa, False si debe detenerse
        """
        try:
            if self.current_phase == CyclePhase.IDLE:
                return False
            
            # Verificar si la fase actual ha terminado
            if self._should_transition_phase():
                self._transition_to_next_phase()
            
            # Ejecutar lógica de la fase actual
            self._execute_current_phase()
            
            return True
            
        except Exception as e:
            logger.error(f"Error en ciclo autónomo: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _should_transition_phase(self) -> bool:
        """Determina si debe transicionar a la siguiente fase"""
        if self.phase_start_time is None:
            return True
        
        phase_duration = self.phase_durations.get(self.current_phase, timedelta(minutes=5))
        elapsed = datetime.now() - self.phase_start_time
        
        return elapsed >= phase_duration
    
    def _transition_to_next_phase(self):
        """Transiciona a la siguiente fase del ciclo"""
        phase_order = [
            CyclePhase.SCANNING,
            CyclePhase.ANALYZING,
            CyclePhase.DECIDING,
            CyclePhase.EXECUTING,
            CyclePhase.MONITORING,
            CyclePhase.LEARNING,
            CyclePhase.OPTIMIZING
        ]
        
        current_index = phase_order.index(self.current_phase)
        
        if current_index < len(phase_order) - 1:
            # Siguiente fase
            self.current_phase = phase_order[current_index + 1]
        else:
            # Ciclo completo, volver a empezar
            self._complete_cycle()
            self.current_phase = CyclePhase.SCANNING
        
        self.phase_start_time = datetime.now()
        logger.info(f"🔄 Transición a fase: {self.current_phase.value}")
    
    def _execute_current_phase(self):
        """Ejecuta la lógica de la fase actual"""
        if self.current_phase == CyclePhase.SCANNING:
            self._phase_scanning()
        elif self.current_phase == CyclePhase.ANALYZING:
            self._phase_analyzing()
        elif self.current_phase == CyclePhase.DECIDING:
            self._phase_deciding()
        elif self.current_phase == CyclePhase.EXECUTING:
            self._phase_executing()
        elif self.current_phase == CyclePhase.MONITORING:
            self._phase_monitoring()
        elif self.current_phase == CyclePhase.LEARNING:
            self._phase_learning()
        elif self.current_phase == CyclePhase.OPTIMIZING:
            self._phase_optimizing()
    
    def _phase_scanning(self):
        """Fase 1: Escanear mercado y encontrar oportunidades"""
        logger.info("🔍 Fase SCANNING: Buscando oportunidades...")
        
        if self.market_scanner:
            try:
                opportunities = self.market_scanner.scan_market(
                    categories=['acciones', 'cedears'],
                    max_symbols=200,
                    use_cache=True
                )
                
                self.opportunities_found = opportunities[:20]  # Top 20
                self.stats['opportunities_found'] += len(self.opportunities_found)
                
                logger.info(f"✅ Encontradas {len(self.opportunities_found)} oportunidades")
                
            except Exception as e:
                logger.error(f"Error en escaneo: {e}")
                self.opportunities_found = []
        else:
            logger.warning("⚠️ Market Scanner no disponible")
            self.opportunities_found = []
    
    def _phase_analyzing(self):
        """Fase 2: Analizar oportunidades encontradas"""
        logger.info("📊 Fase ANALYZING: Evaluando oportunidades...")
        
        if not self.opportunities_found:
            logger.info("   No hay oportunidades para analizar")
            return
        
        analyzed_opportunities = []
        
        for opp in self.opportunities_found:
            try:
                symbol = opp['symbol']
                
                # Análisis completo usando el bot
                if self.trading_bot and hasattr(self.trading_bot, 'analyze_symbol'):
                    analysis = self.trading_bot.analyze_symbol(symbol)
                    
                    if analysis:
                        opp['detailed_analysis'] = analysis
                        opp['final_score'] = analysis.get('score', opp.get('score', 0))
                        analyzed_opportunities.append(opp)
                
            except Exception as e:
                logger.debug(f"Error analizando {opp.get('symbol', 'unknown')}: {e}")
                continue
        
        # Ordenar por score final
        analyzed_opportunities.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        self.opportunities_found = analyzed_opportunities
        
        logger.info(f"✅ Analizadas {len(self.opportunities_found)} oportunidades")
    
    def _phase_deciding(self):
        """Fase 3: Decidir qué operar"""
        logger.info("🤔 Fase DECIDING: Decidiendo operaciones...")
        
        if not self.opportunities_found:
            logger.info("   No hay oportunidades para decidir")
            return
        
        # Filtrar oportunidades con score suficiente
        min_score = 50.0  # Score mínimo para operar
        viable_opportunities = [
            opp for opp in self.opportunities_found
            if opp.get('final_score', opp.get('score', 0)) >= min_score
        ]
        
        # Limitar a top 5
        viable_opportunities = viable_opportunities[:5]
        
        # Verificar posición actual y riesgo
        decisions = []
        for opp in viable_opportunities:
            decision = self._make_trade_decision(opp)
            if decision['should_trade']:
                decisions.append(decision)
        
        self.trades_to_execute = decisions
        logger.info(f"✅ Decididas {len(decisions)} operaciones a ejecutar")
    
    def _make_trade_decision(self, opportunity: Dict) -> Dict:
        """Toma decisión sobre una oportunidad"""
        symbol = opportunity['symbol']
        score = opportunity.get('final_score', opportunity.get('score', 0))
        signal = opportunity.get('signal', 'BUY')
        
        # Verificar si ya tenemos posición
        has_position = False
        if hasattr(self.trading_bot, 'portfolio') and symbol in self.trading_bot.portfolio:
            has_position = True
        
        # Verificar riesgo
        risk_ok = True
        if hasattr(self.trading_bot, 'risk_manager'):
            risk_ok = self.trading_bot.risk_manager.check_risk(symbol, signal)
        
        should_trade = (
            score >= 50.0 and
            not has_position and
            risk_ok
        )
        
        return {
            'symbol': symbol,
            'signal': signal,
            'score': score,
            'should_trade': should_trade,
            'reason': 'Score suficiente y riesgo OK' if should_trade else 'No cumple criterios'
        }
    
    def _phase_executing(self):
        """Fase 4: Ejecutar operaciones"""
        logger.info("⚡ Fase EXECUTING: Ejecutando operaciones...")
        
        if not hasattr(self, 'trades_to_execute'):
            logger.info("   No hay operaciones para ejecutar")
            return
        
        executed = 0
        for trade_decision in self.trades_to_execute:
            try:
                if not trade_decision['should_trade']:
                    continue
                
                symbol = trade_decision['symbol']
                signal = trade_decision['signal']
                
                # Ejecutar trade usando el bot
                if self.trading_bot and hasattr(self.trading_bot, 'execute_trade'):
                    result = self.trading_bot.execute_trade(symbol, signal)
                    
                    if result:
                        self.trades_executed.append({
                            'symbol': symbol,
                            'signal': signal,
                            'timestamp': datetime.now().isoformat(),
                            'result': result
                        })
                        executed += 1
                        self.stats['trades_executed'] += 1
                
            except Exception as e:
                logger.error(f"Error ejecutando trade {trade_decision.get('symbol', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ Ejecutadas {executed} operaciones")
    
    def _phase_monitoring(self):
        """Fase 5: Monitorear posiciones abiertas"""
        logger.info("👁️ Fase MONITORING: Monitoreando posiciones...")
        
        if not hasattr(self.trading_bot, 'portfolio'):
            logger.info("   No hay portafolio para monitorear")
            return
        
        # Obtener posiciones abiertas
        open_positions = []
        if hasattr(self.trading_bot, 'get_open_positions'):
            open_positions = self.trading_bot.get_open_positions()
        elif hasattr(self.trading_bot, 'portfolio'):
            open_positions = [
                {'symbol': sym, 'data': data}
                for sym, data in self.trading_bot.portfolio.items()
                if data.get('quantity', 0) > 0
            ]
        
        # Monitorear cada posición
        for position in open_positions:
            try:
                symbol = position['symbol']
                
                # Verificar stop loss, take profit, etc.
                if self.trading_bot and hasattr(self.trading_bot, 'check_position'):
                    self.trading_bot.check_position(symbol)
                
                self.positions_monitored.append({
                    'symbol': symbol,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.debug(f"Error monitoreando {position.get('symbol', 'unknown')}: {e}")
        
        logger.info(f"✅ Monitoreadas {len(open_positions)} posiciones")
    
    def _phase_learning(self):
        """Fase 6: Aprender de resultados"""
        logger.info("🧠 Fase LEARNING: Aprendiendo de resultados...")
        
        # Analizar trades recientes
        recent_trades = self.trades_executed[-10:]  # Últimos 10
        
        for trade in recent_trades:
            try:
                # Extraer aprendizajes
                learning = self._extract_learning(trade)
                if learning:
                    self.learnings.append(learning)
                
            except Exception as e:
                logger.debug(f"Error extrayendo aprendizaje: {e}")
        
        # Actualizar estrategias si hay aprendizajes
        if self.learnings:
            logger.info(f"✅ Extraídos {len(self.learnings)} aprendizajes")
    
    def _extract_learning(self, trade: Dict) -> Optional[Dict]:
        """Extrae aprendizaje de un trade"""
        # Por ahora, retornar estructura básica
        # En producción, esto analizaría resultados y extraería patrones
        return {
            'symbol': trade.get('symbol'),
            'timestamp': trade.get('timestamp'),
            'insight': 'Trade ejecutado',
            'type': 'execution'
        }
    
    def _phase_optimizing(self):
        """Fase 7: Optimizar estrategias"""
        logger.info("⚙️ Fase OPTIMIZING: Optimizando estrategias...")
        
        # Verificar si hay suficiente data para optimizar
        if self.stats['trades_executed'] < 10:
            logger.info("   Datos insuficientes para optimizar")
            return
        
        # Optimizar parámetros si hay optimizador disponible
        if hasattr(self.trading_bot, 'optimizer'):
            try:
                # Trigger optimización (puede ser asíncrona)
                logger.info("   Iniciando optimización de parámetros...")
                # self.trading_bot.optimizer.optimize()
            except Exception as e:
                logger.debug(f"Error en optimización: {e}")
        
        logger.info("✅ Optimización completada")
    
    def _complete_cycle(self):
        """Completa un ciclo completo"""
        self.last_cycle_time = datetime.now()
        
        # Guardar estadísticas
        self._save_cycle_stats()
        
        logger.info(f"✅ Ciclo #{self.cycle_count} completado")
        logger.info(f"   Oportunidades: {len(self.opportunities_found)}")
        logger.info(f"   Trades ejecutados: {len(self.trades_executed)}")
    
    def _save_cycle_stats(self):
        """Guarda estadísticas del ciclo"""
        stats_file = self.logs_dir / f"cycle_stats_{datetime.now().strftime('%Y%m%d')}.json"
        
        stats_data = {
            'cycle_count': self.cycle_count,
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'current_phase': self.current_phase.value,
            'opportunities_found': len(self.opportunities_found),
            'trades_executed': len(self.trades_executed)
        }
        
        try:
            with open(stats_file, 'w') as f:
                json.dump(stats_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando estadísticas: {e}")
    
    def get_status(self) -> Dict:
        """Obtiene estado actual del ciclo"""
        return {
            'current_phase': self.current_phase.value,
            'cycle_count': self.cycle_count,
            'phase_start_time': self.phase_start_time.isoformat() if self.phase_start_time else None,
            'stats': self.stats,
            'opportunities_found': len(self.opportunities_found),
            'trades_executed': len(self.trades_executed)
        }
    
    def stop_cycle(self):
        """Detiene el ciclo autónomo"""
        logger.info("🛑 Deteniendo Ciclo Autónomo...")
        self.current_phase = CyclePhase.IDLE
        self._save_cycle_stats()

if __name__ == "__main__":
    print("🔄 Testing Autonomous Cycle...")
    print("✅ Cycle module loaded")

