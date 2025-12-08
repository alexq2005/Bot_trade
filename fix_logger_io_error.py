"""
Script para corregir automáticamente las llamadas de logger
Reemplaza logger.warning/error/info/debug con safe_warning/safe_error/etc.
"""
import re
from pathlib import Path

trading_bot_file = Path("trading_bot.py")

if not trading_bot_file.exists():
    print("❌ trading_bot.py no encontrado")
    exit(1)

# Leer el archivo
with open(trading_bot_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya tiene los imports de safe_logger
if "from src.core.safe_logger import" not in content:
    # Agregar import después de get_logger
    content = content.replace(
        "from src.core.logger import get_logger",
        "from src.core.logger import get_logger\nfrom src.core.safe_logger import safe_log, safe_info, safe_error, safe_warning"
    )
    print("✅ Imports de safe_logger agregados")

# Reemplazar llamadas de logger
replacements = [
    (r'logger\.warning\(', 'safe_warning(logger, '),
    (r'logger\.error\(', 'safe_error(logger, '),
    (r'logger\.info\(', 'safe_info(logger, '),
    (r'logger\.debug\(', 'safe_log(logger, "debug", '),
]

changes_made = 0
for pattern, replacement in replacements:
    matches = len(re.findall(pattern, content))
    if matches > 0:
        content = re.sub(pattern, replacement, content)
        changes_made += matches
        print(f"✅ Reemplazadas {matches} llamadas de {pattern}")

if changes_made > 0:
    # Guardar
    with open(trading_bot_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n✅ Total: {changes_made} cambios realizados")
    print("💡 El archivo ha sido actualizado")
else:
    print("ℹ️  No se encontraron llamadas de logger para reemplazar")

