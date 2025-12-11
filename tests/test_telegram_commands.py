import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import traceback
import json
from datetime import datetime

print("DEBUG: Starting test script")

# Add project root to path
try:
    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(root_path)
    print(f"DEBUG: Added to path: {root_path}")
    from trading_bot import TradingBot
    print("DEBUG: Successfully imported TradingBot")
except Exception as e:
    print(f"DEBUG: Error importing TradingBot: {e}")
    traceback.print_exc()
    sys.exit(1)

@patch('trading_bot.IOLClient')
@patch('src.services.telegram_command_handler.TelegramCommandHandler')
@patch('trading_bot.DailyReportService')
@patch('trading_bot.EnhancedSentimentAnalysis')
class TestTelegramCommands(unittest.TestCase):
    def setUp(self, MockSentiment, MockReport, MockTelegram, MockIOL):
        self.mock_telegram = MockTelegram.return_value
        self.mock_report = MockReport.return_value
        self.mock_sentiment = MockSentiment.return_value
        
        # Mock dependencies
        # We don't need to patch load_professional_config here as it's local
        self.bot = TradingBot(paper_trading=True)
            
        # Manually attach mocks that might be overwritten in __init__
        self.bot.telegram_command_handler = self.mock_telegram
        self.bot.daily_report_service = self.mock_report
        self.bot.sentiment_analysis = self.mock_sentiment
        
        # Capture the handlers registered
        self.handlers = {}
        def register_side_effect(command, handler):
            self.handlers[command] = handler
        self.mock_telegram.register_command.side_effect = register_side_effect
        
        # Re-register commands to capture them
        self.bot._register_telegram_commands()

    def test_daily_report_command(self):
        """Test /daily_report command"""
        handler = self.handlers.get('/daily_report')
        self.assertIsNotNone(handler)
        
        # Success case
        self.mock_report.send_daily_report.return_value = True
        handler('123', [])
        self.mock_report.send_daily_report.assert_called_once()
        self.mock_telegram._send_message.assert_any_call('123', "✅ Reporte diario enviado correctamente")

    def test_set_interval_command(self):
        """Test /set_interval command"""
        handler = self.handlers.get('/set_interval')
        self.assertIsNotNone(handler)
        
        # Mock file operations for load/save config
        m = mock_open(read_data='{"analysis_interval_minutes": 60}')
        with patch('builtins.open', m):
            with patch('json.dump') as mock_json_dump:
                # Valid input
                handler('123', '30')
                
                # Verify save was called
                mock_json_dump.assert_called()
                args, _ = mock_json_dump.call_args
                self.assertEqual(args[0]['analysis_interval_minutes'], 30)
                
                self.mock_telegram._send_message.assert_any_call('123', "✅ Intervalo de análisis actualizado a 30 minutos.\n🔄 El cambio se aplicará en el próximo ciclo.")
                
                # Invalid input
                handler('123', 'invalid')
                self.mock_telegram._send_message.assert_any_call('123', "⚠️ Formato incorrecto. Uso: /set_interval <minutos>")

    def test_restarfull_alias(self):
        """Test /restarfull alias exists"""
        self.assertIn('/restarfull', self.handlers)
        self.assertEqual(self.handlers.get('/restarfull'), self.handlers.get('/restart_full'))

    def test_market_command(self):
        """Test /market command"""
        handler = self.handlers.get('/market')
        self.assertIsNotNone(handler)
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_hist = MagicMock()
            mock_hist.__len__.return_value = 2
            mock_hist.__getitem__.return_value.iloc.__getitem__.return_value = 100 # Close price
            mock_ticker.return_value.history.return_value = mock_hist
            
            handler('123', [])
            self.mock_telegram._send_message.assert_called()
            # Check if message contains "Resumen de Mercado"
            args, _ = self.mock_telegram._send_message.call_args
            self.assertIn("Resumen de Mercado", args[1])
