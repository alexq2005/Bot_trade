"""
API REST para Integraciones
Proporciona endpoints para consultar estado, operaciones y controlar el bot
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from typing import Dict, Optional
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/../.."))

from pathlib import Path
from src.core.logger import get_logger
from src.core.health_check import get_health_status
from src.services.operation_notifier import OperationNotifier
from src.services.advanced_learning import AdvancedLearningSystem
from src.services.portfolio_persistence import load_portfolio

logger = get_logger("rest_api")

app = Flask(__name__)
CORS(app)  # Permitir CORS para integraciones


@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint de health check"""
    health = get_health_status()
    return jsonify(health)


@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Obtiene portafolio actual"""
    try:
        portfolio = load_portfolio()
        total_value = sum(p.get('total_val', 0) for p in portfolio) if portfolio else 0
        
        return jsonify({
            'success': True,
            'portfolio': portfolio or [],
            'total_value': total_value,
            'positions_count': len(portfolio) if portfolio else 0,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/operations', methods=['GET'])
def get_operations():
    """Obtiene operaciones recientes"""
    try:
        from pathlib import Path
        import json
        
        operations_file = Path("data/operations_log.json")
        operations = []
        
        if operations_file.exists():
            with open(operations_file, 'r', encoding='utf-8') as f:
                operations = json.load(f)
        
        # Filtrar por parámetros
        limit = request.args.get('limit', 10, type=int)
        op_type = request.args.get('type', None)
        
        filtered = operations
        if op_type:
            filtered = [op for op in operations if op.get('type') == op_type]
        
        filtered = sorted(filtered, key=lambda x: x['timestamp'], reverse=True)[:limit]
        
        return jsonify({
            'success': True,
            'operations': filtered,
            'total': len(operations),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/learning', methods=['GET'])
def get_learning_summary():
    """Obtiene resumen de aprendizaje"""
    try:
        learning_system = AdvancedLearningSystem()
        summary = learning_system.get_learning_summary()
        
        return jsonify({
            'success': True,
            'summary': summary,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bot/status', methods=['GET'])
def bot_status():
    """Estado del bot"""
    try:
        pid_file = Path("bot.pid")
        bot_running = pid_file.exists()
        
        return jsonify({
            'success': True,
            'running': bot_running,
            'timestamp': datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Obtiene alertas recientes"""
    try:
        notifier = OperationNotifier(enable_telegram=False)
        limit = request.args.get('limit', 10, type=int)
        
        alerts = notifier.get_recent_operations(limit)
        
        return jsonify({
            'success': True,
            'alerts': alerts,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Obtiene configuración actual"""
    try:
        from src.core.config_manager import get_config
        
        config = get_config()
        
        return jsonify({
            'success': True,
            'config': config,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    from pathlib import Path
    logger.info("Iniciando API REST en http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)

