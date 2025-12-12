"""
Self-Programming Engine - Motor de Autoprogramación
Permite al bot razonar y mejorarse a sí mismo
"""
import os
import json
import ast
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib


class SelfProgrammingEngine:
    """
    Motor que permite al bot analizar, razonar y mejorarse a sí mismo
    """
    
    def __init__(self, bot_directory: str = ".", max_changes_per_cycle: int = None):
        """
        Args:
            bot_directory: Directorio del bot
            max_changes_per_cycle: Máximo de cambios por ciclo (None = sin límite)
        """
        self.bot_directory = Path(bot_directory)
        self.max_changes_per_cycle = max_changes_per_cycle  # None = sin límite
        self.backup_directory = self.bot_directory / "backups" / "self_programming"
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        
        # Historial de cambios
        self.changes_history_file = self.bot_directory / "data" / "self_programming_history.json"
        self.changes_history = self._load_history()
        
        # Archivos críticos que NO deben modificarse (mínimo absoluto)
        # Solo protegemos el punto de entrada, el resto puede modificarse
        self.protected_files = [
            "run_bot.py",  # Punto de entrada principal (único archivo protegido)
        ]
        
        # Archivos que SÍ pueden modificarse
        self.modifiable_files = [
            "trading_bot.py",
            "src/services/*.py",
            "src/core/*.py",
        ]
        
    def _load_history(self) -> List[Dict]:
        """Carga historial de cambios"""
        if self.changes_history_file.exists():
            try:
                with open(self.changes_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self):
        """Guarda historial de cambios"""
        self.changes_history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.changes_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.changes_history, f, indent=2, ensure_ascii=False)
    
    def analyze_performance(self) -> Dict:
        """
        Analiza el performance del bot para identificar áreas de mejora
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'issues': [],
            'opportunities': [],
            'recommendations': []
        }
        
        # Analizar trades recientes
        trades_file = self.bot_directory / "trades.json"
        if trades_file.exists():
            try:
                with open(trades_file, 'r') as f:
                    trades = json.load(f)
                
                recent_trades = [t for t in trades if t.get('status') == 'FILLED'][-50:]
                
                if recent_trades:
                    wins = [t for t in recent_trades if t.get('pnl', 0) > 0]
                    losses = [t for t in recent_trades if t.get('pnl', 0) < 0]
                    
                    win_rate = len(wins) / len(recent_trades) * 100 if recent_trades else 0
                    avg_win = sum(t.get('pnl', 0) for t in wins) / len(wins) if wins else 0
                    avg_loss = sum(abs(t.get('pnl', 0)) for t in losses) / len(losses) if losses else 0
                    
                    analysis['metrics'] = {
                        'win_rate': win_rate,
                        'avg_win': avg_win,
                        'avg_loss': avg_loss,
                        'total_trades': len(recent_trades),
                        'profit_factor': abs(avg_win / avg_loss) if avg_loss > 0 else 0
                    }
                    
                    # Identificar problemas
                    if win_rate < 50:
                        analysis['issues'].append({
                            'type': 'low_win_rate',
                            'severity': 'high',
                            'description': f'Win rate bajo: {win_rate:.1f}%',
                            'suggestion': 'Ajustar umbrales de entrada o mejorar filtros'
                        })
                    
                    if avg_loss > avg_win * 1.5:
                        analysis['issues'].append({
                            'type': 'poor_risk_reward',
                            'severity': 'high',
                            'description': f'Pérdidas promedio ({avg_loss:.2f}) mucho mayores que ganancias ({avg_win:.2f})',
                            'suggestion': 'Mejorar gestión de stop loss o reducir tamaño de posición'
                        })
                    
                    # Oportunidades
                    if win_rate > 60 and avg_win > 0:
                        analysis['opportunities'].append({
                            'type': 'increase_position_size',
                            'description': 'Performance positivo, considerar aumentar tamaño de posición',
                            'confidence': 'medium'
                        })
            except Exception as e:
                analysis['errors'] = [str(e)]
        
        # Analizar logs de errores
        logs_dir = self.bot_directory / "logs"
        if logs_dir.exists():
            error_logs = list(logs_dir.glob("errors_*.log"))
            if error_logs:
                latest_error_log = max(error_logs, key=lambda p: p.stat().st_mtime)
                try:
                    with open(latest_error_log, 'r', encoding='utf-8', errors='ignore') as f:
                        error_lines = [l for l in f.readlines() if 'ERROR' in l or 'Exception' in l][-20:]
                        if error_lines:
                            analysis['issues'].append({
                                'type': 'recent_errors',
                                'severity': 'medium',
                                'description': f'{len(error_lines)} errores recientes detectados',
                                'suggestion': 'Revisar y corregir errores en logs'
                            })
                except:
                    pass
        
        return analysis
    
    def reason_about_improvements(self, analysis: Dict) -> List[Dict]:
        """
        Razonamiento autónomo sobre mejoras posibles
        """
        improvements = []
        
        # Razonar sobre problemas identificados
        for issue in analysis.get('issues', []):
            if issue['type'] == 'low_win_rate':
                improvements.append({
                    'type': 'adjust_thresholds',
                    'priority': 'high',
                    'description': 'Ajustar umbrales de compra/venta para mejorar win rate',
                    'target_file': 'trading_bot.py',
                    'target_section': 'buy_threshold/sell_threshold',
                    'action': 'increase_buy_threshold',
                    'reasoning': f"Win rate actual {analysis['metrics'].get('win_rate', 0):.1f}% es bajo. Aumentar umbral de compra puede mejorar calidad de trades."
                })
            
            elif issue['type'] == 'poor_risk_reward':
                improvements.append({
                    'type': 'improve_stop_loss',
                    'priority': 'high',
                    'description': 'Mejorar cálculo de stop loss para reducir pérdidas promedio',
                    'target_file': 'src/services/adaptive_risk_manager.py',
                    'target_section': 'calculate_stop_loss',
                    'action': 'tighten_stop_loss',
                    'reasoning': 'Pérdidas promedio son mayores que ganancias. Stop loss más ajustado puede mejorar ratio riesgo/beneficio.'
                })
        
        # Razonar sobre oportunidades
        for opp in analysis.get('opportunities', []):
            if opp['type'] == 'increase_position_size':
                improvements.append({
                    'type': 'optimize_position_sizing',
                    'priority': 'medium',
                    'description': 'Ajustar tamaño de posición basado en performance positivo',
                    'target_file': 'src/services/adaptive_risk_manager.py',
                    'target_section': 'calculate_position_size',
                    'action': 'increase_position_size',
                    'reasoning': 'Win rate y ganancias positivas sugieren que podemos aumentar tamaño de posición con seguridad.'
                })
        
        return improvements
    
    def generate_code_improvement(self, improvement: Dict) -> Optional[str]:
        """
        Genera código mejorado basado en el razonamiento
        """
        action = improvement.get('action')
        target_file = improvement.get('target_file')
        
        if not target_file or not action:
            return None
        
        file_path = self.bot_directory / target_file
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            # Generar código mejorado según la acción
            if action == 'increase_buy_threshold':
                # Buscar y aumentar buy_threshold
                if 'buy_threshold' in original_code:
                    # Incrementar umbral en 5 puntos
                    import re
                    pattern = r"buy_threshold\s*=\s*(\d+)"
                    match = re.search(pattern, original_code)
                    if match:
                        current_threshold = int(match.group(1))
                        new_threshold = current_threshold + 5
                        improved_code = re.sub(
                            pattern,
                            f"buy_threshold = {new_threshold}",
                            original_code
                        )
                        return improved_code
            
            elif action == 'tighten_stop_loss':
                # Buscar y ajustar stop loss
                if 'calculate_stop_loss' in original_code:
                    # Reducir multiplicador ATR para stop loss más ajustado
                    import re
                    pattern = r"(stop_loss\s*=\s*.*?-\s*)(\d+\.?\d*)\s*\*\s*atr"
                    match = re.search(pattern, original_code, re.MULTILINE)
                    if match:
                        multiplier = float(match.group(2))
                        new_multiplier = max(1.0, multiplier - 0.5)  # Reducir pero no menos de 1.0
                        improved_code = re.sub(
                            pattern,
                            f"\\g<1>{new_multiplier} * atr",
                            original_code
                        )
                        return improved_code
            
            elif action == 'increase_position_size':
                # Aumentar tamaño de posición
                if 'calculate_position_size' in original_code:
                    import re
                    pattern = r"(position_size\s*=\s*.*?\*\s*)(\d+\.?\d*)"
                    match = re.search(pattern, original_code, re.MULTILINE)
                    if match:
                        multiplier = float(match.group(2))
                        new_multiplier = min(1.0, multiplier + 0.1)  # Aumentar pero no más de 1.0
                        improved_code = re.sub(
                            pattern,
                            f"\\g<1>{new_multiplier}",
                            original_code
                        )
                        return improved_code
            
        except Exception as e:
            print(f"⚠️  Error generando código: {e}")
            return None
        
        return None
    
    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Valida que el código generado sea sintácticamente correcto
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Error de sintaxis: {e}"
        except Exception as e:
            return False, f"Error validando código: {e}"
    
    def create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Crea backup de un archivo antes de modificarlo
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_directory / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"⚠️  Error creando backup: {e}")
            return None
    
    def apply_improvement(self, improvement: Dict, improved_code: str) -> Dict:
        """
        Aplica una mejora de código de forma segura
        """
        result = {
            'success': False,
            'improvement': improvement,
            'backup_path': None,
            'error': None
        }
        
        target_file = self.bot_directory / improvement['target_file']
        
        # Verificar que el archivo no esté protegido
        if target_file.name in self.protected_files:
            result['error'] = f"Archivo protegido: {target_file.name}"
            return result
        
        # Crear backup
        backup_path = self.create_backup(target_file)
        if not backup_path:
            result['error'] = "No se pudo crear backup"
            return result
        result['backup_path'] = str(backup_path)
        
        # Validar código
        is_valid, error = self.validate_code(improved_code)
        if not is_valid:
            result['error'] = error
            return result
        
        # Aplicar cambio
        try:
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(improved_code)
            
            # Registrar en historial
            change_record = {
                'timestamp': datetime.now().isoformat(),
                'improvement': improvement,
                'backup_path': str(backup_path),
                'file': str(target_file),
                'status': 'applied'
            }
            self.changes_history.append(change_record)
            self._save_history()
            
            result['success'] = True
            return result
            
        except Exception as e:
            result['error'] = f"Error aplicando cambio: {e}"
            # Restaurar desde backup
            try:
                shutil.copy2(backup_path, target_file)
            except:
                pass
            return result
    
    def rollback_change(self, change_record: Dict) -> bool:
        """
        Revierte un cambio aplicado
        """
        try:
            backup_path = Path(change_record['backup_path'])
            target_file = Path(change_record['file'])
            
            if backup_path.exists() and target_file.exists():
                shutil.copy2(backup_path, target_file)
                
                # Marcar como revertido en historial
                change_record['status'] = 'rolled_back'
                change_record['rollback_timestamp'] = datetime.now().isoformat()
                self._save_history()
                
                return True
        except Exception as e:
            print(f"⚠️  Error en rollback: {e}")
        
        return False
    
    def run_improvement_cycle(self) -> Dict:
        """
        Ejecuta un ciclo completo de automejora
        """
        print("\n" + "="*60)
        print("🧠 INICIANDO CICLO DE AUTOPROGRAMACIÓN")
        print("="*60)
        
        # 1. Analizar performance
        print("\n📊 Paso 1: Analizando performance...")
        analysis = self.analyze_performance()
        print(f"   Métricas: Win Rate: {analysis['metrics'].get('win_rate', 0):.1f}%")
        print(f"   Problemas detectados: {len(analysis['issues'])}")
        print(f"   Oportunidades: {len(analysis['opportunities'])}")
        
        # 2. Razonar sobre mejoras
        print("\n🤔 Paso 2: Razonando sobre mejoras...")
        improvements = self.reason_about_improvements(analysis)
        print(f"   Mejoras propuestas: {len(improvements)}")
        
        if not improvements:
            print("\n✅ No se identificaron mejoras necesarias")
            return {
                'success': True,
                'improvements_applied': 0,
                'message': 'No se requieren cambios'
            }
        
        # 3. Aplicar mejoras (sin límites si max_changes_per_cycle es None)
        if self.max_changes_per_cycle is None:
            print(f"\n🔧 Paso 3: Aplicando TODAS las mejoras (sin límites)...")
            improvements_to_apply = improvements
        else:
            print(f"\n🔧 Paso 3: Aplicando mejoras (máx {self.max_changes_per_cycle})...")
            improvements_to_apply = improvements[:self.max_changes_per_cycle]
        
        applied = []
        for improvement in improvements_to_apply:
            print(f"\n   💡 Mejora: {improvement['description']}")
            print(f"      Archivo: {improvement['target_file']}")
            print(f"      Razonamiento: {improvement['reasoning']}")
            
            improved_code = self.generate_code_improvement(improvement)
            if improved_code:
                result = self.apply_improvement(improvement, improved_code)
                if result['success']:
                    print(f"      ✅ Mejora aplicada exitosamente")
                    applied.append(result)
                else:
                    print(f"      ❌ Error: {result['error']}")
            else:
                print(f"      ⚠️  No se pudo generar código mejorado")
        
        print("\n" + "="*60)
        print(f"✅ CICLO COMPLETADO: {len(applied)} mejoras aplicadas")
        print("="*60)
        
        return {
            'success': True,
            'analysis': analysis,
            'improvements_proposed': len(improvements),
            'improvements_applied': len(applied),
            'applied_improvements': applied
        }


# Test
if __name__ == "__main__":
    engine = SelfProgrammingEngine()
    result = engine.run_improvement_cycle()
    print("\nResultado:", json.dumps(result, indent=2, ensure_ascii=False))

