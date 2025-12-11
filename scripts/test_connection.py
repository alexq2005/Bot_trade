# -*- coding: utf-8 -*-
"""
Prueba de conexión con el cliente IOL.
"""
import sys
import os

# Añadir el directorio raíz al path para poder importar desde src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test2_bot_trade')))

from src.connectors.iol_client import IOLClient

def test_iol_connection():
    """
    Realiza una prueba de conexión simple con la API de IOL.
    """
    print("Iniciando prueba de conexión con IOL...")
    try:
        client = IOLClient()
        status = client.get_account_status()
        
        if status and isinstance(status, dict) and "estado" in status:
            print("✅ Conexión exitosa.")
            print(f"   Estado de la cuenta: {status['estado']}")
            print(f"   Tipo de cuenta: {status.get('tipo', 'N/A')}")
            print(f"   Número de cuenta: {status.get('numero', 'N/A')}")
        elif status and isinstance(status, dict) and "error" not in status:
            print("✅ Conexión exitosa.")
            print(f"   Respuesta de IOL recibida correctamente")
            # Mostrar estructura de la respuesta
            if "cuentas" in status:
                print(f"   Cuentas encontradas: {len(status['cuentas'])}")
        else:
            print("❌ Error: La respuesta de la API no tiene el formato esperado.")
            print(f"   Respuesta recibida: {status}")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO durante la conexión: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_iol_connection()

