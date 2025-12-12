"""
Script de prueba para ejecutar una operación REAL de compra en IOL
IMPORTANTE: Este script ejecuta el bot en modo LIVE TRADING con dinero real
"""
import sys
import os
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.append(str(Path(__file__).parent))

from trading_bot import TradingBot
from src.connectors.iol_client import IOLClient
from datetime import datetime

def verificar_conexion_iol():
    """Verifica la conexión con IOL"""
    print("="*60)
    print("🔍 VERIFICANDO CONEXIÓN CON IOL")
    print("="*60)
    
    try:
        iol = IOLClient()
        
        # Verificar saldo disponible
        print("\n1️⃣ Verificando saldo disponible...")
        saldo = iol.get_available_balance()
        print(f"   ✅ Saldo disponible: ${saldo:,.2f} ARS")
        
        # Verificar cuenta
        print("\n2️⃣ Verificando información de cuenta...")
        cuenta = iol.get_account_info()
        if cuenta:
            print(f"   ✅ Cuenta: {cuenta.get('numero', 'N/A')}")
            print(f"   ✅ Tipo: {cuenta.get('tipo', 'N/A')}")
            print(f"   ✅ Estado: {cuenta.get('estado', 'N/A')}")
        
        # Verificar símbolos disponibles
        print("\n3️⃣ Verificando símbolos disponibles...")
        print("   💡 El bot usará los símbolos configurados")
        
        return True, saldo
        
    except Exception as e:
        print(f"   ❌ Error conectando con IOL: {e}")
        return False, 0

def ejecutar_bot_live():
    """Ejecuta el bot en modo LIVE TRADING"""
    print("\n" + "="*60)
    print("🚀 INICIANDO BOT EN MODO LIVE TRADING")
    print("="*60)
    print("\n⚠️  ADVERTENCIA: Este bot operará con DINERO REAL")
    print("⚠️  Asegúrate de haber revisado la configuración")
    print("⚠️  El bot ejecutará operaciones reales en IOL\n")
    
    # Confirmación
    respuesta = input("¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
    if respuesta.upper() != 'SI':
        print("❌ Operación cancelada por el usuario")
        return
    
    # Verificar conexión primero
    conexion_ok, saldo = verificar_conexion_iol()
    if not conexion_ok:
        print("\n❌ No se pudo conectar con IOL. Abortando...")
        return
    
    if saldo < 1000:
        print(f"\n⚠️  Saldo bajo: ${saldo:,.2f} ARS")
        print("⚠️  Se recomienda tener al menos $1,000 ARS para operar")
        respuesta = input("¿Continuar de todas formas? (SI/NO): ")
        if respuesta.upper() != 'SI':
            print("❌ Operación cancelada")
            return
    
    # Configurar símbolos (puedes modificar esto)
    # Por defecto, usar algunos símbolos comunes de Argentina
    simbolos = ['AAPL', 'GGAL', 'PAMP']  # Puedes cambiar estos
    
    print(f"\n📊 Símbolos a monitorear: {', '.join(simbolos)}")
    print(f"💰 Capital disponible: ${saldo:,.2f} ARS")
    
    try:
        # Crear bot en modo LIVE (paper_trading=False)
        print("\n🤖 Creando bot en modo LIVE TRADING...")
        bot = TradingBot(
            symbols=simbolos,
            initial_capital=saldo,
            paper_trading=False  # ⚠️ MODO LIVE - DINERO REAL
        )
        
        print("\n✅ Bot creado exitosamente")
        print("\n📋 Configuración:")
        print(f"   • Modo: LIVE TRADING (dinero real)")
        print(f"   • Símbolos: {', '.join(simbolos)}")
        print(f"   • Capital: ${saldo:,.2f} ARS")
        print(f"   • Gestión de riesgo: ACTIVA")
        print(f"   • Stop loss: ACTIVO")
        print(f"   • Take profit: ACTIVO")
        
        # Ejecutar UN ciclo de análisis
        print("\n" + "="*60)
        print("🔄 EJECUTANDO CICLO DE ANÁLISIS")
        print("="*60)
        print("\nEl bot analizará los símbolos y ejecutará trades si encuentra señales BUY")
        print("Presiona Ctrl+C para detener en cualquier momento\n")
        
        # Ejecutar un ciclo
        resultados = bot.run_analysis_cycle()
        
        # Mostrar resultados
        print("\n" + "="*60)
        print("📊 RESULTADOS DEL CICLO")
        print("="*60)
        
        if resultados:
            for resultado in resultados:
                simbolo = resultado.get('symbol', 'N/A')
                señal = resultado.get('final_signal', 'N/A')
                score = resultado.get('score', 0)
                
                print(f"\n📈 {simbolo}:")
                print(f"   • Señal: {señal}")
                print(f"   • Score: {score:.2f}")
                
                if señal == 'BUY':
                    print(f"   ✅ SEÑAL DE COMPRA DETECTADA")
                    print(f"   💰 El bot debería haber ejecutado una compra")
                elif señal == 'SELL':
                    print(f"   🔴 SEÑAL DE VENTA DETECTADA")
                else:
                    print(f"   ⏸️  HOLD - No hay señal clara")
        else:
            print("\n⚠️  No se generaron resultados")
        
        print("\n" + "="*60)
        print("✅ CICLO COMPLETADO")
        print("="*60)
        print("\n💡 Revisa los logs y el archivo trades.json para ver las operaciones ejecutadas")
        print("💡 También puedes revisar tu cuenta en IOL para confirmar las operaciones")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Bot detenido por el usuario")
    except Exception as e:
        print(f"\n\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 PRUEBA DE OPERACIÓN REAL EN IOL")
    print("="*60)
    print("\nEste script ejecutará el bot en modo LIVE TRADING")
    print("El bot analizará símbolos y ejecutará compras si encuentra señales BUY")
    print("\n⚠️  ADVERTENCIA: Se usará DINERO REAL")
    print("="*60 + "\n")
    
    ejecutar_bot_live()

