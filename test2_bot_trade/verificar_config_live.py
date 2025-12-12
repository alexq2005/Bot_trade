"""
Script para verificar configuración antes de iniciar modo LIVE
"""
import json
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def verificar_configuracion():
    """Verifica que la configuración esté lista para modo LIVE"""
    print("=" * 60)
    print("🔍 VERIFICANDO CONFIGURACIÓN PARA MODO LIVE")
    print("=" * 60)
    print()
    
    errores = []
    advertencias = []
    
    # 1. Verificar credenciales IOL
    print("1️⃣ Verificando credenciales IOL...")
    iol_username = os.getenv('IOL_USERNAME')
    iol_password = os.getenv('IOL_PASSWORD')
    
    if not iol_username:
        errores.append("❌ IOL_USERNAME no configurado en .env")
    else:
        print(f"   ✅ IOL_USERNAME: {iol_username[:3]}***")
    
    if not iol_password:
        errores.append("❌ IOL_PASSWORD no configurado en .env")
    else:
        print(f"   ✅ IOL_PASSWORD: Configurado")
    
    print()
    
    # 2. Verificar configuración de riesgo
    print("2️⃣ Verificando configuración de riesgo...")
    config_file = Path("professional_config.json")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        risk_per_trade = config.get('risk_per_trade', 0)
        max_daily_loss = config.get('max_daily_loss_pct', 0)
        max_position_size = config.get('max_position_size_pct', 0)
        
        print(f"   • Riesgo por trade: {risk_per_trade * 100:.2f}%")
        print(f"   • Pérdida máxima diaria: {max_daily_loss}%")
        print(f"   • Tamaño máximo de posición: {max_position_size}%")
        
        if risk_per_trade > 0.05:
            advertencias.append(f"⚠️  Riesgo por trade alto: {risk_per_trade * 100:.2f}% (recomendado < 5%)")
        
        if max_daily_loss > 10:
            advertencias.append(f"⚠️  Pérdida máxima diaria alta: {max_daily_loss}% (recomendado < 10%)")
        
        if max_position_size > 20:
            advertencias.append(f"⚠️  Tamaño máximo de posición alto: {max_position_size}% (recomendado < 20%)")
    else:
        errores.append("❌ professional_config.json no encontrado")
    
    print()
    
    # 3. Verificar capital disponible
    print("3️⃣ Verificando capital...")
    print("   💡 El bot obtendrá el capital disponible de IOL automáticamente")
    print("   💡 Asegúrate de tener suficiente capital para operar")
    print()
    
    # 4. Verificar stop loss y take profit
    print("4️⃣ Verificando stop loss y take profit...")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        stop_loss = config.get('stop_loss_atr_multiplier', 0)
        take_profit = config.get('take_profit_atr_multiplier', 0)
        
        print(f"   • Stop Loss: {stop_loss}x ATR")
        print(f"   • Take Profit: {take_profit}x ATR")
        
        if stop_loss == 0:
            advertencias.append("⚠️  Stop Loss no configurado - RIESGO ALTO")
        
        if take_profit == 0:
            advertencias.append("⚠️  Take Profit no configurado")
    print()
    
    # 5. Verificar Telegram (opcional pero recomendado)
    print("5️⃣ Verificando notificaciones Telegram...")
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat = os.getenv('TELEGRAM_CHAT_ID')
    
    if telegram_token and telegram_chat:
        print("   ✅ Telegram configurado - Recibirás notificaciones")
    else:
        advertencias.append("⚠️  Telegram no configurado - No recibirás notificaciones de trades")
    print()
    
    # Resumen
    print("=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print()
    
    if errores:
        print("❌ ERRORES CRÍTICOS (debes corregirlos antes de iniciar):")
        for error in errores:
            print(f"   {error}")
        print()
        print("⚠️  NO inicies el bot en modo LIVE hasta corregir estos errores")
        return False
    else:
        print("✅ No hay errores críticos")
        print()
    
    if advertencias:
        print("⚠️  ADVERTENCIAS (revisa antes de iniciar):")
        for advertencia in advertencias:
            print(f"   {advertencia}")
        print()
    
    print("=" * 60)
    print("✅ CONFIGURACIÓN VERIFICADA")
    print("=" * 60)
    print()
    print("💡 RECOMENDACIONES ANTES DE INICIAR:")
    print("   1. Prueba primero en modo PAPER TRADING")
    print("   2. Verifica que el bot funcione correctamente")
    print("   3. Revisa tus límites de riesgo")
    print("   4. Asegúrate de tener capital suficiente")
    print("   5. Monitorea las primeras operaciones de cerca")
    print()
    print("🚀 Para iniciar en modo LIVE:")
    print("   python run_bot.py --live --continuous")
    print("   O usa: iniciar_live_trading.bat")
    print()
    
    return len(errores) == 0

if __name__ == "__main__":
    verificar_configuracion()

