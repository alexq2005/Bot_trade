# 🔗 Guía de Integración de Features

Cómo integrar features desarrolladas en `test_bot/` al bot principal.

---

## 📋 Proceso de Integración Paso a Paso

### Paso 1: Validar Feature Standalone ✅

```bash
# Probar la feature de forma aislada
python test_bot/features/mi_feature.py

# Ejecutar tests
python test_bot/tests/test_mi_feature.py
```

**Criterio de éxito**: Feature ejecuta sin errores y tests pasan

---

### Paso 2: Agregar Feature Flag 🚩

Editar `professional_config.json`:

```json
{
  "features": {
    "mi_feature": false  // ← Agregar feature desactivada
  },
  
  "feature_configs": {
    "mi_feature": {       // ← Agregar config específica
      "param1": "valor1",
      "param2": 100
    }
  }
}
```

**⚠️ IMPORTANTE**: Agregar la feature como `false` inicialmente

---

### Paso 3: Integrar en trading_bot.py 🔧

Ubicación: Método `__init__()` de la clase `TradingBot`

```python
def __init__(self, symbols=None, initial_capital=None, paper_trading=True):
    # ... código existente ...
    
    # AL FINAL del __init__, antes de cerrar:
    
    # Inicializar features opcionales
    self._init_optional_features()

def _init_optional_features(self):
    """Inicializa features opcionales según feature flags"""
    features = self.config.get('features', {})
    
    # Mi Feature
    if features.get('mi_feature', False):
        try:
            from test_bot.features.mi_feature import MiFeature
            feature_config = self.config.get('feature_configs', {}).get('mi_feature', {})
            self.mi_feature = MiFeature(config=feature_config)
            print("✅ Mi Feature activada")
        except ImportError as e:
            print(f"⚠️  Mi Feature no disponible: {e}")
            self.mi_feature = None
        except Exception as e:
            print(f"❌ Error inicializando Mi Feature: {e}")
            self.mi_feature = None
    else:
        self.mi_feature = None
```

**Ventajas de este enfoque**:
- ✅ Si la feature falla, el bot continúa funcionando
- ✅ Se puede activar/desactivar sin cambiar código
- ✅ Fácil rollback (solo cambiar flag a `false`)

---

### Paso 4: Usar la Feature en el Bot 🎯

Ubicación: Donde necesites usar la feature

```python
def run_analysis_cycle(self):
    # ... código existente ...
    
    # Usar feature si está disponible y activada
    if self.mi_feature:
        try:
            resultado = self.mi_feature.ejecutar(parametro1="valor")
            print(f"✅ Mi Feature ejecutada: {resultado}")
        except Exception as e:
            print(f"⚠️  Error en Mi Feature (continuando normalmente): {e}")
            # El bot continúa aunque la feature falle
    
    # ... resto del código ...
```

**Patrón de uso seguro**:
```python
if self.mi_feature:  # Verificar que existe
    try:  # Siempre en try/except
        # Usar la feature
        pass
    except Exception as e:
        # Manejar error sin romper el bot
        print(f"⚠️  Error: {e}")
```

---

### Paso 5: Probar en Paper Trading 📊

```bash
# 1. Activar feature en config
# professional_config.json: "mi_feature": true

# 2. Ejecutar bot en paper trading
python run_bot.py --paper --continuous

# 3. Monitorear logs
tail -f logs/*.log  # Linux/Mac
Get-Content logs/*.log -Wait  # Windows

# 4. Observar por 24-48 horas
# - Sin errores críticos
# - Feature funciona como esperado
# - No degrada rendimiento
```

---

### Paso 6: Deploy a Producción 🚀

```bash
# 1. Detener bot de producción
# (Desde Telegram: /detener)
# O manualmente: taskkill /F /PID [PID]

# 2. Crear backup pre-deploy
python backup_estado_estable.py "pre_deploy_mi_feature"

# 3. Activar feature en producción
# professional_config.json: "mi_feature": true

# 4. Iniciar bot
python run_bot.py --live --continuous

# 5. Monitorear primeras 2 horas
# Revisar logs cada 15 minutos
# Verificar que feature funciona
# Confirmar que no hay errores

# 6. Si todo OK → Feature integrada ✅
# 7. Si hay problemas → Rollback
```

---

## 🔄 Rollback de Feature

Si una feature causa problemas en producción:

### Opción 1: Desactivar Feature Flag (Rápido)

```bash
# 1. Editar professional_config.json
#    "mi_feature": false

# 2. Reiniciar bot
# (No necesita restaurar código)
```

### Opción 2: Restaurar Backup Completo (Si es necesario)

```bash
# 1. Listar backups
python restaurar_backup.py

# 2. Restaurar backup específico
python restaurar_backup.py stable_20251202_114451_pre_test_bot_estructura

# 3. Reiniciar bot
```

---

## 📊 Ejemplos de Integración Exitosa

### Ejemplo 1: Backtesting V2

**Desarrollo**:
```python
# test_bot/features/backtester_v2.py
class BacktesterV2:
    def __init__(self, config):
        self.config = config
    
    def run_backtest(self, symbol, strategy):
        # Implementación
        return {"profit": 1500, "win_rate": 0.65}
```

**Integración en trading_bot.py**:
```python
def _init_optional_features(self):
    if self.config.get('features', {}).get('backtesting_v2', False):
        from test_bot.features.backtester_v2 import BacktesterV2
        self.backtester = BacktesterV2(self.config.get('feature_configs', {}).get('backtesting_v2', {}))
```

**Uso**:
```python
# Comando Telegram: /backtest AAPL
def handle_backtest(chat_id, args):
    if self.backtester:
        result = self.backtester.run_backtest(args, strategy="default")
        self.telegram_command_handler._send_message(chat_id, f"Resultado: {result}")
```

---

### Ejemplo 2: API REST

**Desarrollo**:
```python
# test_bot/features/api_rest.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/status")
def get_status():
    return {"status": "running"}

def start_api_server(bot_instance):
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

**Integración**:
```python
def _init_optional_features(self):
    if self.config.get('features', {}).get('api_rest', False):
        from test_bot.features.api_rest import start_api_server
        import threading
        
        api_thread = threading.Thread(
            target=start_api_server,
            args=(self,),
            daemon=True
        )
        api_thread.start()
        print("✅ API REST iniciada en http://localhost:8000")
```

---

## ⚠️ Errores Comunes y Soluciones

### Error: ImportError al integrar

**Causa**: Python no encuentra el módulo en `test_bot/`

**Solución**:
```python
# En trading_bot.py, al inicio del archivo:
import sys
from pathlib import Path

# Agregar test_bot al path
sys.path.append(str(Path(__file__).parent / "test_bot"))

# Ahora los imports funcionarán
from features.mi_feature import MiFeature
```

### Error: Feature rompe el bot

**Causa**: Exception no manejada en la feature

**Solución**: Siempre usar try/except al llamar features:
```python
if self.mi_feature:
    try:
        self.mi_feature.ejecutar()
    except Exception as e:
        # Loggear pero continuar
        logger.error(f"Error en feature: {e}")
        # El bot sigue funcionando
```

### Error: Conflicto de configuración

**Causa**: Feature modifica config de producción

**Solución**: Usar config separada:
```python
# En la feature, NO modificar professional_config.json
# En su lugar, usar testing_config.json
```

---

## 📝 Checklist de Integración Completa

```
Pre-Integración:
□ Feature desarrollada en test_bot/features/
□ Tests creados en test_bot/tests/
□ Probada standalone exitosamente
□ Documentada en test_bot/docs/
□ Backup creado antes de integrar

Integración:
□ Feature flag agregada (desactivada)
□ Feature config agregada
□ Código integrado en trading_bot.py
□ Imports con try/except
□ Uso de feature con validación

Testing:
□ Probada con feature flag activada
□ Paper trading 24-48h sin errores
□ Logs revisados (sin errores críticos)
□ Rendimiento no degradado
□ Funcionalidad existente no afectada

Post-Integración:
□ Feature activada en producción
□ Monitoreada primeras 2-4 horas
□ CHANGELOG.md actualizado
□ Documentación actualizada
□ Backup post-integración creado
```

---

## 🎯 Buenas Prácticas

1. **Desarrolla incrementalmente**: No intentes hacer todo de una vez
2. **Prueba frecuentemente**: Ejecuta tests después de cada cambio significativo
3. **Documenta mientras desarrollas**: No dejes la documentación para el final
4. **Mantén el bot funcionando**: Nunca detengas el bot de producción por largo tiempo
5. **Comunica cambios**: Actualiza CHANGELOG.md y comenta el código
6. **Usa feature flags**: Facilitan activar/desactivar sin cambiar código
7. **Valida exhaustivamente**: Mejor prevenir que lamentar
8. **Backup frecuente**: Antes y después de cambios importantes

---

**🤖 Desarrollado por Antigravity + Claude**

