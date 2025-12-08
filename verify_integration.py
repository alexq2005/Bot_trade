
import json
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.services.adaptive_risk_manager import AdaptiveRiskManager
from src.services.auto_configurator import AutoConfigurator

def verify_integration():
    print("🔍 Verifying Configuration Integration...")
    
    config_file = "professional_config.json"
    if not os.path.exists(config_file):
        print(f"❌ Config file {config_file} not found!")
        return False
        
    with open(config_file, 'r') as f:
        config = json.load(f)
        
    print(f"✅ Config file found: {config_file}")
    
    # Check AdaptiveRiskManager
    risk_manager = AdaptiveRiskManager()
    
    # Check if parameters match config
    expected_pos_size = config.get("max_position_size_pct", 18) / 100
    if abs(risk_manager.base_position_size_pct - expected_pos_size) < 0.001:
        print(f"✅ AdaptiveRiskManager loaded correct position size: {risk_manager.base_position_size_pct*100}%")
    else:
        print(f"❌ AdaptiveRiskManager mismatch! Expected {expected_pos_size}, got {risk_manager.base_position_size_pct}")
        return False
        
    # Check AutoConfigurator
    auto_config = AutoConfigurator()
    if auto_config.config_file == config_file:
        print(f"✅ AutoConfigurator using correct config file: {auto_config.config_file}")
    else:
        print(f"❌ AutoConfigurator using wrong config file: {auto_config.config_file}")
        return False
        
    print("\n✅ Integration Verification PASSED!")
    return True

if __name__ == "__main__":
    verify_integration()
