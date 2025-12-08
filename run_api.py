"""
Script para ejecutar la API REST
"""
import os
import sys
from pathlib import Path

# Configurar path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

import uvicorn
from src.api.main import app

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    print(f"🚀 Iniciando API en http://localhost:{port}")
    print(f"📚 Documentación: http://localhost:{port}/docs")
    print(f"🏥 Health Check: http://localhost:{port}/health")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

