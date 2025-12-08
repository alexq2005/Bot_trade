# 📊 Dos Modos de Portafolio

## 🎯 Configuración Dual Implementada

El bot ahora soporta **2 modos de gestión de portafolio**:

---

## 📋 MODO 1: PORTAFOLIO COMPLETO

**Configuración:** `only_iol_portfolio: false`

**Qué incluye:**
- ✅ Activos en IOL (operables)
- ✅ Activos en Tienda Broker (no operables en IOL)
- ✅ Activos importados manualmente (CSV)

**Archivo:** `my_portfolio.json`

**Uso:** Para **visualización** y **seguimiento** de todos tus activos

**Ejemplo:**
```
IOL:
- GGAL: 100 acciones
- YPFD: 50 acciones

Tienda Broker:
- METR: 200 acciones (NO operable en IOL)
- CEPU: 150 acciones

Total símbolos: 4
```

**Ventajas:**
- ✅ Ves TODOS tus activos en un solo lugar
- ✅ Dashboard muestra valor total real
- ✅ Monitoreo completo de patrimonio

**Limitación:**
- ⚠️ El bot NO puede operar activos que no estén en IOL
- ⚠️ Solo monitorea y alerta

---

## 💰 MODO 2: SOLO IOL

**Configuración:** `only_iol_portfolio: true`

**Qué incluye:**
- ✅ SOLO activos disponibles en IOL
- ❌ Sin Tienda Broker
- ❌ Sin activos no operables

**Fuente:** `iol_client.get_portfolio()` (API en vivo)

**Uso:** Para **trading activo** con el bot

**Ejemplo:**
```
IOL:
- GGAL: 100 acciones ✅ OPERABLE
- YPFD: 50 acciones ✅ OPERABLE

Total símbolos: 2 (todos operables)
```

**Ventajas:**
- ✅ TODOS los símbolos son operables
- ✅ El bot puede comprar/vender cualquiera
- ✅ Sincronización automática con IOL
- ✅ Más simple y directo

**Ideal para:**
- Trading automático
- Operaciones en LIVE
- Máxima eficiencia

---

## ⚙️ CONFIGURACIÓN

### En professional_config.json:

```json
{
  "monitoring": {
    "only_iol_portfolio": false,  // ← Cambiar aquí
    "auto_sync_portfolio": true,
    "max_symbols": 100,
    
    // false = MODO COMPLETO (IOL + Tienda Broker)
    // true  = MODO SOLO_IOL (solo operables)
  }
}
```

---

## 🔄 FLUJO DE CADA MODO

### Modo COMPLETO (only_iol_portfolio: false):

```
1. Bot carga my_portfolio.json
   ↓
2. Contiene activos de:
   - IOL (sincronizados)
   - Tienda Broker (importados)
   - CSV (manuales)
   ↓
3. Extrae TODOS los símbolos
   ↓
4. Monitorea todos (operable o no)
   ↓
5. Solo ejecuta trades en símbolos disponibles en IOL
```

### Modo SOLO_IOL (only_iol_portfolio: true):

```
1. Bot llama sync_from_iol(iol_client)
   ↓
2. sync_from_iol obtiene portafolio de IOL
   ↓
3. Guarda temporalmente en my_portfolio.json
   ↓
4. Extrae símbolos
   ↓
5. TODOS son operables
```

---

## 🎯 RECOMENDACIÓN DE USO

### Para Paper Trading:
- **Usar:** MODO COMPLETO
- **Por qué:** Puedes monitorear todos tus activos sin riesgo

### Para Live Trading:
- **Usar:** MODO SOLO_IOL
- **Por qué:** 
  - Evita confusión con activos no operables
  - El bot solo monitorea lo que puede operar
  - Más eficiente y seguro

---

## 📊 VISUALIZACIÓN EN DASHBOARD

### Gestión de Activos → Mi Portafolio:

**Modo COMPLETO:**
```
📊 Resumen del Portafolio
💰 Valor Total: $850,000 (IOL + Tienda Broker)
📦 Total Activos: 26

Activos:
✅ GGAL (IOL - operable)
✅ YPFD (IOL - operable)
📊 METR (Tienda Broker - solo seguimiento)
📊 CEPU (Tienda Broker - solo seguimiento)
```

**Modo SOLO_IOL:**
```
📊 Resumen del Portafolio IOL
💰 Valor Total: $650,000 (solo IOL)
📦 Total Activos: 18

Activos:
✅ GGAL (operable)
✅ YPFD (operable)
✅ PAMP (operable)
```

---

## 🔧 CAMBIAR DE MODO

### Opción 1: Archivo de Configuración

```bash
# Editar professional_config.json
"only_iol_portfolio": false  # COMPLETO
"only_iol_portfolio": true   # SOLO_IOL
```

### Opción 2: Dashboard (próximamente)

```
Dashboard → Gestión de Activos → Configuración
[ ] Solo IOL (activos operables)
[x] Completo (IOL + Tienda Broker)
```

---

## 💾 ARCHIVOS

### my_portfolio.json:

**Modo COMPLETO:**
- Contiene activos de todas las fuentes
- Algunos operables, otros no

**Modo SOLO_IOL:**
- Contiene SOLO activos de IOL
- Todos operables
- Se actualiza cada vez que inicias el bot

---

## 📝 RESUMEN

| Característica | COMPLETO | SOLO_IOL |
|----------------|----------|----------|
| **Fuentes** | IOL + TB + CSV | Solo IOL API |
| **Total símbolos** | 20-30+ | 10-20 |
| **Todos operables** | ❌ No | ✅ Sí |
| **Uso** | Seguimiento | Trading |
| **Recomendado para** | Paper Trading | Live Trading |
| **Sincronización** | Manual | Automática |

---

**Configuración actual:** `only_iol_portfolio: false` → **MODO COMPLETO**

**Para cambiar a SOLO_IOL:** Edita `professional_config.json` y pon `true`

---

**¿Quieres cambiar a SOLO_IOL ahora o dejar COMPLETO?** 🎯

