# 🕵️‍♀️ FASE 3: Checklist de Auditoría de Lógica Profunda

Jules, usa esta lista para revisar línea por línea los componentes críticos.

## 1. Módulo de Trading Manual (`terminal_manual_simplified.py`)
>
> **Riesgo:** Precios estancados o botones que no responden.

- [ ] **PriceService Cache:** Verificar que `get_price()` tenga un mecanismo para limpiar caché (`force_refresh=True`) cuando el usuario cambia de símbolo manualmente.
- [ ] **Streamlit State:** Confirmar que usamos `st.session_state['symbol']` y callbacks `on_change` para resetear inputs. Si ves `st.rerun()` ejecutándose en un loop infinito (dentro del `render` sin condición), **es un bug**.
- [ ] **Feedback Visual:** ¿El usuario ve un spinner o mensaje de "Orden Enviada"? El código debe manejar bloqueos de UI.

## 2. Bot Autónomo (`trading_bot.py` / `watchdog.py`)
>
> **Riesgo:** Baneo de API o Crash silencioso.

- [ ] **IOL Rate Limiting:** Busca llamadas a `time.sleep()`. Si el bot hace `while True` sin dormir al menos 1-5 segundos entre llamadas a la API, **bloquéalo**. IOL permite ~1-2 req/segundo.
- [ ] **Token Refresh:** Simula que el token expira (puedes invalidarlo manualmente en el debugger). ¿El bot lanza `Exception` y muere, o captura, re-autentica y sigue?
- [ ] **Stop Loss en Memoria:** Si el bot se reinicia, ¿pierde el "precio de compra original" para calcular el Stop Loss? Debe persistirse en `trades.json` o base de datos.

## 3. Persistencia (`src/services/portfolio_persistence.py`)
>
> **Riesgo:** Pérdida de dinero (datos).

- [ ] **Atomic Writes:** Al guardar `trades.json`, ¿escribe directamente o usa archivo temporal + rename? Si crashea escribiendo, el archivo se corrompe.
  - *Patrón correcto:* `json.dump` a `temp_trades.json` -> `os.replace('temp.json', 'trades.json')`.
- [ ] **Recovery:** Si `trades.json` está vacío o corrupto, ¿el código asume Portfolio vacío o intenta buscar backups?

## 4. Gestión de Errores Global (`dashboard.py`)

- [ ] **Global Catch:** ¿Hay un `try/except Exception` genérico que envuelva el `main()`? Debe haberlo para loggearlo en disco antes de cerrar.

---
**Entregable:** Marca con [x] lo revisado y corregido. Si encuentras algo roto, crea una ISSUE o arréglalo inmediatamente.
