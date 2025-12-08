"""
Training Monitor Service
Monitors training progress in real-time and provides updates.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TrainingMonitor:
    """
    Service to monitor training progress in real-time.
    """
    
    def __init__(self):
        self.training_log_file = "training_log.json"
        self.training_metrics_file = "training_metrics.json"
    
    def get_training_status(self, symbol: Optional[str] = None) -> Dict:
        """
        Get current training status.
        
        Args:
            symbol: Optional symbol to check status for
        
        Returns:
            Dictionary with training status
        """
        status = {
            "is_training": False,
            "current_symbol": None,
            "progress": 0,
            "epoch": 0,
            "total_epochs": 0,
            "loss": None,
            "val_loss": None,
            "start_time": None,
            "elapsed_time": None
        }
        
        # Check if training_metrics.json exists and was recently updated
        if os.path.exists(self.training_metrics_file):
            try:
                with open(self.training_metrics_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                
                # Check if training is recent (within last 10 minutes)
                if 'timestamp' in metrics:
                    timestamp = datetime.fromisoformat(metrics['timestamp'])
                    elapsed = (datetime.now() - timestamp).total_seconds()
                    
                    if elapsed < 600:  # 10 minutes
                        status["is_training"] = True
                        status["current_symbol"] = metrics.get('symbol')
                        status["loss"] = metrics.get('loss')
                        status["val_loss"] = metrics.get('val_loss')
                        status["epoch"] = metrics.get('epochs', 0)
                        status["total_epochs"] = metrics.get('epochs', 50)
                        status["progress"] = min(100, (status["epoch"] / status["total_epochs"] * 100) if status["total_epochs"] > 0 else 0)
            except Exception:
                pass
        
        return status
    
    def get_training_logs(self, symbol: Optional[str] = None, lines: int = 50) -> List[str]:
        """
        Get recent training logs.
        
        Args:
            symbol: Optional symbol to filter logs
            lines: Number of lines to return
        
        Returns:
            List of log lines
        """
        logs = []
        
        # Check error_log.txt for training errors
        if os.path.exists('error_log.txt'):
            try:
                with open('error_log.txt', 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    # Get last N lines
                    logs.extend([line.strip() for line in all_lines[-lines:] if 'Training' in line or 'train_model' in line])
            except Exception:
                pass
        
        # Check if there's a training log file
        if os.path.exists(self.training_log_file):
            try:
                with open(self.training_log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    if isinstance(log_data, list):
                        logs.extend([entry.get('message', '') for entry in log_data[-lines:]])
            except Exception:
                pass
        
        return logs
    
    def get_training_history(self) -> List[Dict]:
        """
        Get training history from training_metrics.json.
        
        Returns:
            List of training records
        """
        history = []
        
        if os.path.exists(self.training_metrics_file):
            try:
                with open(self.training_metrics_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                    if isinstance(metrics, dict):
                        history.append(metrics)
            except Exception:
                pass
        
        return history
    
    def monitor_training_process(self, process, symbol: str) -> Dict:
        """
        Monitor a training process in real-time.
        
        Args:
            process: subprocess.Popen object
            symbol: Symbol being trained
        
        Returns:
            Dictionary with monitoring results
        """
        start_time = time.time()
        output_lines = []
        error_lines = []
        
        # Read output in real-time
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                if not line:
                    break
                output_lines.append(line.strip())
                # Limit to last 100 lines
                if len(output_lines) > 100:
                    output_lines.pop(0)
        
        if process.stderr:
            for line in iter(process.stderr.readline, ''):
                if not line:
                    break
                error_lines.append(line.strip())
                if len(error_lines) > 100:
                    error_lines.pop(0)
        
        elapsed_time = time.time() - start_time
        
        return {
            "symbol": symbol,
            "elapsed_time": elapsed_time,
            "output": output_lines,
            "errors": error_lines,
            "returncode": process.returncode if hasattr(process, 'returncode') else None
        }


def get_training_status(symbol: Optional[str] = None) -> Dict:
    """
    Convenience function to get training status.
    
    Args:
        symbol: Optional symbol to check
    
    Returns:
        Dictionary with training status
    """
    monitor = TrainingMonitor()
    return monitor.get_training_status(symbol)

