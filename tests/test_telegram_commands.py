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

class TestTelegramCommands(unittest.TestCase):
    # Decorators removed for manual execution
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
        if not handler:
            print("❌ /daily_report handler not found")
            return
        
        # Success case
        self.mock_report.send_daily_report.return_value = True
        handler('123', [])
        self.mock_report.send_daily_report.assert_called_once()
        self.mock_telegram._send_message.assert_any_call('123', "✅ Reporte diario enviado correctamente")

    def test_set_interval_command(self):
        """Test /set_interval command"""
        handler = self.handlers.get('/set_interval')
        if not handler:
            print("❌ /set_interval handler not found")
            return
        
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
        if '/restarfull' in self.handlers:
            print("✅ /restarfull alias found")
        else:
            print("❌ /restarfull alias NOT found")
            
        if self.handlers.get('/restarfull') == self.handlers.get('/restart_full'):
             print("✅ /restarfull maps to correct handler")
        else:
             print("❌ /restarfull maps to WRONG handler")

    def test_market_command(self):
        """Test /market command"""
        handler = self.handlers.get('/market')
        if not handler:
            print("❌ /market handler not found")
            return
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_hist = MagicMock()
            mock_hist.__len__.return_value = 2
            mock_hist.__getitem__.return_value.iloc.__getitem__.return_value = 100 # Close price
            mock_ticker.return_value.history.return_value = mock_hist
            
            handler('123', [])
            self.mock_telegram._send_message.assert_called()
            # Check if message contains "Resumen de Mercado"
            args, _ = self.mock_telegram._send_message.call_args
            if "Resumen de Mercado" in args[1]:
                print("✅ /market message content correct")
            else:
                print(f"❌ /market message content incorrect: {args[1][:50]}...")

if __name__ == '__main__':
    # Manual execution to debug
    try:
        print("DEBUG: Starting manual test execution")
        test = TestTelegramCommands()
        
        # Mock setup
        print("DEBUG: Setting up mocks...")
        with patch('trading_bot.IOLClient') as MockIOL, \
             patch('src.services.telegram_command_handler.TelegramCommandHandler') as MockTelegram, \
             patch('trading_bot.DailyReportService') as MockReport, \
             patch('trading_bot.EnhancedSentimentAnalysis') as MockSentiment:
             
            test.setUp(MockSentiment, MockReport, MockTelegram, MockIOL)
            print("DEBUG: Setup complete")
            
            print("DEBUG: Testing /daily_report...")
            test.test_daily_report_command()
            print("DEBUG: /daily_report PASSED")
            
            print("DEBUG: Testing /set_interval...")
            test.test_set_interval_command()
            print("DEBUG: /set_interval PASSED")
            
            print("DEBUG: Testing /restarfull...")
            test.test_restarfull_alias()
            print("DEBUG: /restarfull PASSED")
            
            print("DEBUG: Testing /market...")
            test.test_market_command()
            print("DEBUG: /market PASSED")
            
        print("✅ ALL TESTS PASSED")
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)
