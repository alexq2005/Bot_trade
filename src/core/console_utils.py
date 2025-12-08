"""
Console Utilities for Windows Compatibility
Utilidades para manejar problemas de codificación en Windows
"""
import sys
import os

def setup_windows_console():
    """
    Configura la consola de Windows para soportar UTF-8 y evitar errores de Unicode.
    Debe llamarse al inicio de scripts que usan emojis o caracteres especiales.
    """
    if sys.platform == 'win32':
        try:
            import io
            # Configurar stdout y stderr para UTF-8
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, 
                    encoding='utf-8', 
                    errors='replace',
                    line_buffering=True
                )
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, 
                    encoding='utf-8', 
                    errors='replace',
                    line_buffering=True
                )
            
            # Intentar configurar la consola de Windows para UTF-8
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleOutputCP(65001)  # UTF-8
            except:
                pass  # Si falla, al menos tenemos el wrapper
                
        except Exception:
            pass  # Si falla, continuar sin cambios


def safe_print(message: str, use_emoji: bool = True):
    """
    Imprime un mensaje de forma segura, reemplazando emojis si es necesario.
    
    Args:
        message: Mensaje a imprimir
        use_emoji: Si False, reemplaza emojis comunes con texto
    """
    if not use_emoji and sys.platform == 'win32':
        # Reemplazar emojis comunes con texto
        replacements = {
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '🔄': '[REFRESH]',
            '📊': '[CHART]',
            '💰': '[MONEY]',
            '🚀': '[ROCKET]',
            '🛡️': '[SHIELD]',
            '📈': '[UP]',
            '📉': '[DOWN]',
            '💡': '[IDEA]',
            '🔍': '[SEARCH]',
            '📝': '[NOTE]',
            '💸': '[CASH]',
            '🧪': '[TEST]',
            '🎯': '[TARGET]',
            '🤖': '[BOT]',
            '📱': '[PHONE]',
            '🛑': '[STOP]',
        }
        for emoji, text in replacements.items():
            message = message.replace(emoji, text)
    
    try:
        print(message)
    except UnicodeEncodeError:
        # Si aún falla, usar ASCII seguro
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        print(safe_message)

