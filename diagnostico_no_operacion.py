"""
Script para diagnosticar por qué el bot no operó
Verifica: horario de mercado, saldo, filtros, scores, etc.
"""
import json
from pathlib import Path
from datetime import datetime, time
import os

def verificar_horario_mercado():
    """Verifica si el mercado está abierto según los filtros del bot"""
    print("\n" + "="*70)
    print("⏰ VERIFICACIÓN DE HORARIO DE MERCADO")
    print("="*70)
    
    try:
        from src.services.professional_trader import ProfessionalTrader
        trader = ProfessionalTrader()
        
        can_trade, reason = trader.check_time_filters()
        
        now = datetime.now()
        current_time = now.time()
        weekday = now.strftime("%A")
        
        print(f"\n📅 Fecha y Hora Actual:")
        print(f"   • Día: {weekday}")
        print(f"   • Hora: {current_time.strftime('%H:%M:%S')}")
        
        # Obtener configuración de horarios
        time_config = trader.config.get("time_management", {})
        start_time = time_config.get("trading_hours_start", "09:30")
        end_time = time_config.get("trading_hours_end", "16:00")
        
        print(f"\n🕐 Horario de Trading Configurado:")
        print(f"   • Inicio: {start_time}")
        print(f"   • Fin: {end_time}")
        
        if can_trade:
            print(f"\n✅ {reason}")
            print("   → El mercado está ABIERTO según la configuración")
        else:
            print(f"\n❌ {reason}")
            print("   → El mercado está CERRADO según la configuración")
            print("   → El bot NO operará hasta que el mercado abra")
        
        return can_trade, reason
        
    except Exception as e:
        print(f"\n⚠️  Error verificando horario: {e}")
        return None, str(e)

def verificar_saldo():
    """Verifica el saldo disponible en IOL"""
    print("\n" + "="*70)
    print("💰 VERIFICACIÓN DE SALDO")
    print("="*70)
    
    try:
        from src.connectors.iol_client import IOLClient
        iol = IOLClient()
        
        balance = iol.get_available_balance()
        
        print(f"\n💵 Saldo Disponible en IOL:")
        print(f"   • ${balance:,.2f} ARS")
        
        # Verificar si hay suficiente saldo para una operación mínima
        # Asumir que una operación mínima requiere al menos $10,000 ARS
        min_required = 10000.0
        
        if balance >= min_required:
            print(f"\n✅ Saldo suficiente para operar")
            print(f"   → Tienes ${balance:,.2f} disponible")
            print(f"   → Mínimo recomendado: ${min_required:,.2f}")
        else:
            print(f"\n⚠️  Saldo bajo")
            print(f"   → Tienes ${balance:,.2f} disponible")
            print(f"   → Mínimo recomendado: ${min_required:,.2f}")
            print(f"   → Puede que no haya suficiente saldo para operar")
        
        return balance
        
    except Exception as e:
        print(f"\n❌ Error obteniendo saldo: {e}")
        return None

def verificar_filtros():
    """Verifica otros filtros que pueden bloquear operaciones"""
    print("\n" + "="*70)
    print("🛡️  VERIFICACIÓN DE FILTROS")
    print("="*70)
    
    try:
        from src.services.adaptive_risk_manager import AdaptiveRiskManager
        risk_manager = AdaptiveRiskManager(initial_capital=100000)
        
        can_trade, reason = risk_manager.can_trade()
        
        print(f"\n📊 Estado del Risk Manager:")
        print(f"   • Operaciones diarias: {risk_manager.daily_trades_count}/{risk_manager.max_daily_trades}")
        print(f"   • P&L diario: ${risk_manager.daily_pnl:,.2f}")
        print(f"   • Pérdidas consecutivas: {risk_manager.consecutive_losses}")
        print(f"   • Capital actual: ${risk_manager.current_capital:,.2f}")
        print(f"   • Capital inicial: ${risk_manager.initial_capital:,.2f}")
        
        if can_trade:
            print(f"\n✅ {reason}")
            print("   → El Risk Manager permite operar")
        else:
            print(f"\n❌ {reason}")
            print("   → El Risk Manager está BLOQUEANDO operaciones")
        
        return can_trade, reason
        
    except Exception as e:
        print(f"\n⚠️  Error verificando risk manager: {e}")
        return None, str(e)

def verificar_scores_recientes():
    """Verifica los scores recientes de análisis"""
    print("\n" + "="*70)
    print("📊 VERIFICACIÓN DE SCORES RECIENTES")
    print("="*70)
    
    operations_file = Path("data/operations_log.json")
    
    if not operations_file.exists():
        print("\n⚠️  No se encontró operations_log.json")
        print("   → El bot puede no haber ejecutado análisis aún")
        return
    
    try:
        with open(operations_file, 'r', encoding='utf-8') as f:
            operations = json.load(f)
        
        # Filtrar análisis recientes
        analyses = [
            op for op in operations 
            if op.get('type') == 'ANALYSIS' and op.get('data', {}).get('score') is not None
        ]
        
        if not analyses:
            print("\n⚠️  No hay análisis recientes con scores")
            print("   → El bot puede no haber ejecutado análisis aún")
            return
        
        # Ordenar por timestamp
        analyses.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        recent = analyses[:5]
        
        # Cargar umbrales
        config_file = Path("professional_config.json")
        buy_threshold = 20
        sell_threshold = -20
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    buy_threshold = config.get('buy_threshold', 20)
                    sell_threshold = config.get('sell_threshold', -20)
            except:
                pass
        
        print(f"\n📈 Últimos 5 Análisis:")
        print(f"   • Umbral de compra: {buy_threshold}")
        print(f"   • Umbral de venta: {sell_threshold}")
        print()
        
        for op in recent:
            data = op.get('data', {})
            symbol = data.get('symbol', 'N/A')
            score = data.get('score', 0)
            signal = data.get('final_signal', 'HOLD')
            filter_reason = data.get('filter_reason')
            timestamp = op.get('timestamp', 'N/A')
            
            # Formatear timestamp
            if timestamp != 'N/A':
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            operaria = (signal == 'BUY' and score >= buy_threshold) or (signal == 'SELL' and score <= sell_threshold)
            
            status_emoji = "✅" if operaria else "⏸️"
            status_text = "OPERARÍA" if operaria else "NO OPERARÍA"
            
            print(f"   {status_emoji} {symbol:8s} | Score: {score:4d} | {signal:4s} | {status_text}")
            if filter_reason:
                print(f"      ⚠️  Bloqueado: {filter_reason}")
            print(f"      📅 {timestamp}")
            print()
        
    except Exception as e:
        print(f"\n⚠️  Error leyendo análisis: {e}")

def verificar_logs_recientes():
    """Verifica los logs recientes del bot"""
    print("\n" + "="*70)
    print("📝 VERIFICACIÓN DE LOGS RECIENTES")
    print("="*70)
    
    # Buscar archivos de log
    log_files = []
    if os.path.exists("logs"):
        log_files = [f for f in os.listdir("logs") if f.endswith(".log")]
    
    if not log_files:
        print("\n⚠️  No se encontraron archivos de log")
        return
    
    latest_log = max([os.path.join("logs", f) for f in log_files], key=os.path.getmtime)
    
    try:
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Buscar mensajes relevantes
        relevant_messages = []
        keywords = [
            "Filtro de Tiempo",
            "Filtro de Entrada",
            "Trade blocked",
            "Insufficient balance",
            "Score:",
            "Final Signal:",
            "Starting Analysis Cycle",
            "Horario válido",
            "Horario no válido"
        ]
        
        # Últimas 100 líneas
        for line in lines[-100:]:
            for keyword in keywords:
                if keyword.lower() in line.lower():
                    relevant_messages.append(line.strip())
                    break
        
        if relevant_messages:
            print(f"\n📋 Mensajes Relevantes (últimas {len(relevant_messages)}):")
            for msg in relevant_messages[-10:]:  # Últimas 10
                print(f"   • {msg}")
        else:
            print("\n⚠️  No se encontraron mensajes relevantes en los logs")
            print("   → El bot puede no haber ejecutado análisis aún")
            
    except Exception as e:
        print(f"\n⚠️  Error leyendo logs: {e}")

def main():
    """Función principal"""
    print("="*70)
    print("🔍 DIAGNÓSTICO: ¿Por qué el bot no operó?")
    print("="*70)
    
    # 1. Verificar horario
    can_trade_time, time_reason = verificar_horario_mercado()
    
    # 2. Verificar saldo
    balance = verificar_saldo()
    
    # 3. Verificar filtros
    can_trade_risk, risk_reason = verificar_filtros()
    
    # 4. Verificar scores
    verificar_scores_recientes()
    
    # 5. Verificar logs
    verificar_logs_recientes()
    
    # Resumen final
    print("\n" + "="*70)
    print("📋 RESUMEN Y CONCLUSIÓN")
    print("="*70)
    
    problemas = []
    soluciones = []
    
    if can_trade_time is False:
        problemas.append(f"⏰ Mercado cerrado: {time_reason}")
        soluciones.append("   💡 Espera a que el mercado abra o ajusta los horarios en la configuración")
    
    if balance is not None and balance < 10000:
        problemas.append(f"💰 Saldo bajo: ${balance:,.2f} ARS")
        soluciones.append("   💡 Deposita más fondos en IOL o reduce el tamaño de las posiciones")
    
    if can_trade_risk is False:
        problemas.append(f"🛡️  Risk Manager bloqueando: {risk_reason}")
        soluciones.append("   💡 Revisa los límites de riesgo o espera a que se reseteen los contadores diarios")
    
    if not problemas:
        print("\n✅ No se encontraron problemas obvios")
        print("   → El bot puede estar esperando señales con scores suficientes")
        print("   → Revisa los scores recientes arriba")
        print("   → Verifica que los umbrales no sean demasiado altos")
    else:
        print("\n❌ Problemas encontrados:")
        for problema in problemas:
            print(f"   {problema}")
        
        print("\n💡 Soluciones:")
        for solucion in soluciones:
            print(solucion)
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()

