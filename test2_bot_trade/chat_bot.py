"""
Chat Bot - Interfaz de chat interactiva
Permite conversar con el bot de forma espontánea
"""
import sys
from pathlib import Path

# Agregar directorio al path
sys.path.insert(0, str(Path(__file__).parent))

from src.services.chat_interface import ChatInterface


def main():
    """Inicia el chat interactivo"""
    print("\n" + "="*60)
    print("🤖 BOT DE TRADING - CHAT INTERACTIVO")
    print("="*60)
    print("\nEl bot puede:")
    print("  • Razonar de forma espontánea")
    print("  • Buscar información en internet")
    print("  • Aprender de las conversaciones")
    print("  • Mejorarse basado en intereses")
    print("\n" + "="*60 + "\n")
    
    # Inicializar chat
    chat = ChatInterface()
    
    # Iniciar conversación interactiva
    chat.interactive_chat()


if __name__ == "__main__":
    main()

