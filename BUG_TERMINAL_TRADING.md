# 🐛 BUG REPORT - Terminal de Trading

**Fecha:** 2024-12-11 23:00 ART  
**Reportado por:** Usuario (Lexus)  
**Prioridad:** 🔴 ALTA  
**Componente:** Dashboard - Terminal de Trading

---

## 📋 Descripción del Problema

**Ubicación:** Dashboard > Terminal de Trading > Manual Trading

**Síntomas:**

1. ❌ Al seleccionar un activo, el precio NO se actualiza
2. ❌ Los precios se mantienen estáticos
3. ❌ El símbolo en "Precio Actual" NO cambia cuando se selecciona un activo diferente

---

## 🔍 Comportamiento Esperado vs Actual

### Comportamiento Esperado ✅

1. Usuario selecciona un activo (ej: GGAL)
2. El sistema obtiene el precio actual de IOL
3. Se muestra "Precio Actual GGAL: $7,470.00"
4. Usuario cambia a otro activo (ej: YPFD)
5. El precio se actualiza automáticamente
6. Se muestra "Precio Actual YPFD: $[nuevo precio]"

### Comportamiento Actual ❌

1. Usuario selecciona un activo (ej: GGAL)
2. Se muestra un precio
3. Usuario cambia a otro activo (ej: YPFD)
4. ❌ El precio NO cambia
5. ❌ El símbolo sigue mostrando el anterior
6. ❌ Los precios permanecen estáticos

---

## 📍 Ubicación del Código

**Archivo afectado:**

```
test2_bot_trade/src/dashboard/views/terminal_manual_simplified.py
```

**Función específica:**

- Selector de símbolos
- Obtención de precios
- Actualización de `st.metric()`

---

## 🔧 Análisis Técnico

### Posibles Causas

1. **Cache de Streamlit:**
   - El precio puede estar en cache y no se invalida al cambiar símbolo
   - `st.cache_data` o `st.cache_resource` no se está limpiando

2. **Session State:**
   - El símbolo seleccionado no se está guardando correctamente en `st.session_state`
   - La actualización del estado no dispara re-render

3. **PriceService:**
   - El servicio de precios puede estar devolviendo valores cacheados
   - No se está pasando el símbolo correcto al servicio

4. **st.metric() sin key:**
   - Ya se eliminó el parámetro `key` anteriormente
   - Pero puede que necesite un identificador único para forzar actualización

---

## 🧪 Pasos para Reproducir

1. Iniciar dashboard: `streamlit run test2_bot_trade/dashboard.py`
2. Navegar a: Terminal de Trading
3. Ir a tab: "Manual Trading Directo"
4. Seleccionar un activo (ej: GGAL)
5. Observar el precio mostrado
6. Cambiar a otro activo (ej: YPFD)
7. **BUG:** El precio NO cambia, símbolo NO cambia

---

## 🔍 Código a Revisar

### terminal_manual_simplified.py

**Líneas críticas a revisar:**

- Selector de símbolos (selectbox)
- Llamada a PriceService
- Actualización de st.metric()
- Manejo de st.session_state

**Verificar:**

```python
# ¿El símbolo se está guardando correctamente?
selected_symbol = st.selectbox("Seleccionar Activo", symbols, key="symbol_selector")

# ¿Se está obteniendo el precio correcto?
current_price = price_service.get_price(selected_symbol)

# ¿st.metric() se está actualizando?
st.metric(
    label=f"Precio Actual {selected_symbol}",
    value=f"${current_price:,.2f}",
    delta=f"🕒 {timestamp_str}",
    delta_color="off"
)
```

---

## 💡 Soluciones Propuestas

### Solución 1: Forzar Invalidación de Cache

```python
# Agregar timestamp o símbolo al cache key
@st.cache_data(ttl=60)
def get_price_cached(symbol, timestamp):
    return price_service.get_price(symbol)

current_price = get_price_cached(selected_symbol, int(time.time()))
```

### Solución 2: Usar Session State Correctamente

```python
# Guardar símbolo en session state
if 'current_symbol' not in st.session_state:
    st.session_state.current_symbol = symbols[0]

selected_symbol = st.selectbox(
    "Seleccionar Activo",
    symbols,
    index=symbols.index(st.session_state.current_symbol),
    key="symbol_selector"
)

# Detectar cambio
if selected_symbol != st.session_state.current_symbol:
    st.session_state.current_symbol = selected_symbol
    st.rerun()
```

### Solución 3: Usar Unique Key en Metric

```python
# Crear key único basado en símbolo y timestamp
metric_key = f"price_{selected_symbol}_{int(time.time())}"

st.metric(
    label=f"Precio Actual {selected_symbol}",
    value=f"${current_price:,.2f}",
    delta=f"🕒 {timestamp_str}",
    delta_color="off"
)
```

---

## 🎯 Tareas para Jules

### 1. Investigación

- [ ] Revisar `terminal_manual_simplified.py` línea por línea
- [ ] Verificar cómo se maneja el selector de símbolos
- [ ] Verificar cómo se obtienen los precios
- [ ] Verificar el cache de PriceService

### 2. Debugging

- [ ] Agregar prints de debug para ver qué símbolo se selecciona
- [ ] Verificar qué precio se obtiene de IOL
- [ ] Verificar si st.metric() se está actualizando

### 3. Corrección

- [ ] Implementar una de las soluciones propuestas
- [ ] Probar que el cambio de símbolo actualice el precio
- [ ] Verificar que el símbolo en "Precio Actual" cambie

### 4. Testing

- [ ] Probar con múltiples símbolos
- [ ] Verificar que los precios se actualicen correctamente
- [ ] Confirmar que no hay regresiones

### 5. Documentación

- [ ] Documentar la solución implementada
- [ ] Actualizar el reporte de testing
- [ ] Subir cambios a Git

---

## 📊 Impacto

**Severidad:** 🔴 ALTA  
**Usuarios Afectados:** Todos los que usen Terminal de Trading  
**Funcionalidad Afectada:** Trading Manual - Funcionalidad principal

---

## ⏰ Prioridad

**ALTA - Requiere corrección inmediata**

Este bug afecta la funcionalidad principal del Terminal de Trading, impidiendo que los usuarios vean precios actualizados de diferentes activos.

---

## 📝 Notas Adicionales

- El reporte de testing de Jules indicó que todo funcionaba
- Es posible que el bug solo se manifieste en uso real, no en tests automatizados
- Puede ser un problema de timing o de interacción con Streamlit

---

**JULES: Por favor investiga y corrige este bug URGENTEMENTE.**

---

**Reportado por:** Usuario (Lexus)  
**Fecha:** 2024-12-11 23:00 ART  
**Estado:** 🔴 ABIERTO - Pendiente de corrección
