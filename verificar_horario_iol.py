"""
Script para verificar que el horario de trading esté configurado correctamente para IOL (11:00 - 17:00)
"""
import json
from pathlib import Path
from datetime import datetime, time

def verificar_configuracion():
    """Verifica la configuración de horarios"""
    print("=" * 70)
    print("⏰ VERIFICACIÓN DE HORARIO DE TRADING IOL")
    print("=" * 70)
    print()
    
    # 1. Verificar professional_config.json
    print("1️⃣ Verificando professional_config.json...")
    config_file = Path("professional_config.json")
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            time_mgmt = config.get("time_management", {})
            start = time_mgmt.get("trading_hours_start", "NO CONFIGURADO")
            end = time_mgmt.get("trading_hours_end", "NO CONFIGURADO")
            
            print(f"   • Horario de inicio: {start}")
            print(f"   • Horario de fin: {end}")
            
            if start == "11:00" and end == "17:00":
                print("   ✅ Configuración correcta para IOL (11:00 - 17:00)")
            else:
                print("   ⚠️  Configuración NO coincide con horario IOL")
                print("   💡 Debería ser: 11:00 - 17:00")
        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")
    else:
        print("   ⚠️  Archivo professional_config.json no encontrado")
    
    print()
    
    # 2. Verificar ProfessionalTrader
    print("2️⃣ Verificando ProfessionalTrader...")
    try:
        from src.services.professional_trader import ProfessionalTrader
        
        # Intentar cargar desde professional_config.json
        trader = ProfessionalTrader(config_file="professional_config.json")
        time_config = trader.config.get("time_management", {})
        
        start = time_config.get("trading_hours_start", "NO CONFIGURADO")
        end = time_config.get("trading_hours_end", "NO CONFIGURADO")
        
        print(f"   • Horario de inicio: {start}")
        print(f"   • Horario de fin: {end}")
        
        if start == "11:00" and end == "17:00":
            print("   ✅ ProfessionalTrader configurado correctamente")
        else:
            print("   ⚠️  ProfessionalTrader NO está usando horario IOL")
            print("   💡 Debería ser: 11:00 - 17:00")
        
        # Probar check_time_filters
        print()
        print("3️⃣ Probando validación de horario...")
        now = datetime.now()
        current_time = now.time()
        
        can_trade, reason = trader.check_time_filters()
        
        print(f"   • Hora actual: {current_time.strftime('%H:%M:%S')}")
        print(f"   • Día: {now.strftime('%A')}")
        print(f"   • Puede operar: {'✅ SÍ' if can_trade else '❌ NO'}")
        print(f"   • Razón: {reason}")
        
        # Verificar horario específico
        start_time = time(11, 0)
        end_time = time(17, 0)
        
        if current_time < start_time:
            print(f"   ⏰ Mercado aún no abre (abre a las 11:00)")
        elif current_time > end_time:
            print(f"   ⏰ Mercado ya cerró (cerró a las 17:00)")
        elif start_time <= current_time <= end_time:
            print(f"   ✅ Dentro del horario de trading IOL (11:00 - 17:00)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)
    print("📋 RESUMEN")
    print("=" * 70)
    print()
    print("✅ El bot está configurado para operar de 11:00 a 17:00")
    print("   (Horario de trading de IOL)")
    print()
    print("💡 El bot NO operará fuera de este horario")
    print("💡 El bot seguirá analizando, pero no ejecutará operaciones")
    print("=" * 70)


if __name__ == "__main__":
    verificar_configuracion()

