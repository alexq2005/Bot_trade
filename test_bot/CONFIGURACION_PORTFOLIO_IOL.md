# 📊 Configuración: Solo Portafolio de IOL

## ✅ CAMBIOS APLICADOS

**Fecha:** Diciembre 3, 2025  
**Objetivo:** Simplificar gestión de símbolos usando **SOLO** el portafolio real de IOL

---

## 🔄 QUÉ SE CAMBIÓ

### Antes:
```
Fuentes de símbolos (en orden):
1. my_portfolio.json (local)
2. Tienda Broker (web scraping)
3. Símbolos adicionales (configuración)
4. Base de datos (entrenamiento)
5. Símbolos por defecto

❌ Complejo
❌ Múltiples fuentes
❌ Posibles inconsistencias
```

### Ahora:
```
Fuente ÚNICA de símbolos:
1. iol_client.get_portfolio() (API de IOL)

✅ Simple
✅ Una sola fuente de verdad
✅ Siempre sincronizado con tu cuenta real
```

---

## 🔧 IMPLEMENTACIÓN

### En trading_bot.py (líneas 230-270):

```python
# NUEVO: SOLO USAR PORTAFOLIO DE IOL
self.portfolio = []  # Inicializar vacío

if symbols is None or len(symbols) == 0:
    print("📊 OBTENIENDO PORTAFOLIO DESDE IOL")
    
    # Sincronizar portafolio desde IOL
    from src.services.portfolio_persistence import sync_from_iol
    if sync_from_iol(self.iol_client):
        # Cargar portafolio recién sincronizado
        from src.services.portfolio_persistence import load_portfolio
        self.portfolio = load_portfolio()
        
        # Extraer símbolos
        for p in self.portfolio:
            symbol = p.get('symbol', '').strip()
            if symbol:
                symbols.append(symbol)
        
        print(f"✅ Portafolio de IOL: {len(symbols)} símbolos")
    else:
        print("⚠️  No se pudo sincronizar con IOL")
```

### En professional_config.json:

```json
"monitoring": {
  "use_portfolio_symbols": true,
  "auto_sync_portfolio": true,
  "only_iol_portfolio": true,  // ← NUEVO
  "additional_symbols": [],    // ← Vacío
  "max_symbols": 100
}
```

---

## 🚀 CÓMO FUNCIONA

### Flujo de Inicio del Bot:

```
1. Bot se conecta a IOL
   ↓
2. Llama a sync_from_iol(iol_client)
   ↓
3. sync_from_iol obtiene portafolio real de IOL
   ↓
4. Guarda en my_portfolio.json (solo para persistencia)
   ↓
5. Bot carga símbolos desde portafolio sincronizado
   ↓
6. Monitorea SOLO esos símbolos
```

**Fuente de verdad:** API de IOL  
**Archivo local:** Solo caché para persistencia

---

## 📊 QUÉ OBTIENE DE IOL

### Datos del Portafolio:

```python
# iol_client.get_portfolio() retorna:
[
    {
        "symbol": "GGAL",
        "quantity": 100,
        "avg_price": 7800.00,
        "current_price": 8200.00,
        "total_val": 820000.00,
        "pnl": 40000.00,
        "pnl_pct": 5.13
    },
    {
        "symbol": "YPFD",
        "quantity": 50,
        ...
    }
]
```

**El bot monitoreará TODOS estos símbolos automáticamente.**

---

## ✅ VENTAJAS

1. **🎯 Siempre sincronizado**
   - El portafolio del bot = tu portafolio real
   - No hay inconsistencias

2. **🔄 Actualización automática**
   - Cada vez que inicias el bot, sincroniza con IOL
   - Si compras/vendes manualmente en IOL, el bot lo detecta

3. **🧹 Simplicidad**
   - Una sola fuente de verdad
   - Menos archivos de configuración
   - Menos puntos de fallo

4. **📊 Precisión**
   - Cantidad real de acciones
   - Precio promedio real
   - P&L real

---

## ⚙️ CONFIGURACIÓN

### professional_config.json:

```json
{
  "monitoring": {
    "use_portfolio_symbols": true,      // Usar portafolio
    "auto_sync_portfolio": true,        // Sincronizar automáticamente
    "only_iol_portfolio": true,         // SOLO IOL (sin otros)
    "additional_symbols": [],           // Sin adicionales
    "max_symbols": 100                  // Límite (por seguridad)
  }
}
```

**Todos los flags en `true` para asegurar sincronización.**

---

## 🔍 VERIFICACIÓN

### Para verificar que funciona:

```python
# En el inicio del bot, verás:
📊 OBTENIENDO PORTAFOLIO DESDE IOL
============================================================
✅ Portafolio sincronizado desde IOL
📂 ✅ Portafolio de IOL: 26 símbolos
   PAMP, BYMA, AMZN, CEPU, BA37D, NU, EDN, TGNO4, ...
```

### Si algo falla:

```python
❌ Error obteniendo portafolio de IOL: [mensaje de error]
📌 Usando símbolos por defecto temporales:
   GGAL, YPFD, PAMP

💡 Consejo: Verifica tu conexión a IOL y recarga el bot
```

---

## 🔧 MANTENIMIENTO

### Agregar/Quitar Activos:

**Método correcto:**
1. Compra/Vende el activo en IOL (tu broker)
2. Reinicia el bot
3. El bot detectará el cambio automáticamente

**NO es necesario:**
- ❌ Editar `my_portfolio.json`
- ❌ Editar configuración
- ❌ Sincronizar manualmente

### Sincronización Manual (Dashboard):

Si quieres forzar una sincronización sin reiniciar el bot:
1. Dashboard → "💼 Gestión de Activos"
2. Tab "📥 Sincronizar IOL"
3. Click en "🔄 Sincronizar Holdings (Solo IOL)"

---

## 📁 ARCHIVOS AFECTADOS

### Modificados:
- `test_bot/trading_bot.py` (líneas 230-270)
- `test_bot/professional_config.json` (línea 18-23)

### Ya NO se usan:
- ❌ `my_portfolio.json` (solo como caché)
- ❌ Tienda Broker scraping
- ❌ Símbolos adicionales manuales
- ❌ Símbolos de base de datos

### Se SIGUE usando:
- ✅ `iol_client.get_portfolio()` (API de IOL)
- ✅ `sync_from_iol()` (sincronización)

---

## 🎯 RESULTADO FINAL

**El bot ahora es más simple y preciso:**
- ✅ Una sola fuente de datos (IOL)
- ✅ Siempre sincronizado con tu cuenta real
- ✅ Menos configuración manual
- ✅ Más confiable

**Tu portafolio en IOL = Portafolio del bot** ✨

---

## 🚀 PRÓXIMOS PASOS

1. **Reiniciar el bot** para aplicar cambios
2. **Verificar** que cargue símbolos de IOL correctamente
3. **Confirmar** que muestra tu portafolio real

**Comando:**
```bash
cd test_bot
python run_bot.py --paper --continuous
```

---

**Desarrollado con IA por Antigravity**  
**Diciembre 3, 2025**

