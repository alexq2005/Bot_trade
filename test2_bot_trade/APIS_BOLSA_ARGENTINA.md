# 📊 APIs de la Bolsa de Valores Argentina - Revisión y Recomendaciones

## 🔍 APIs Disponibles

### 1. **BYMA (Bolsas y Mercados Argentinos)**
**URL:** https://www.byma.com.ar/byma-apis

**Características:**
- ✅ API de Market Data: Precios negociados en el día
- ✅ API de Índices: Dólar BYMA, Dólar CCL
- ⚠️ Requiere homologación
- ⚠️ Disponible exclusivamente para Agentes Miembros de BYMA
- ⚠️ Puede tener costos asociados

**Limitaciones:**
- No es pública (requiere membresía)
- Proceso de homologación necesario
- Principalmente para datos en tiempo real, no históricos completos

---

### 2. **MAE (Mercado Abierto Electrónico)**
**URL:** https://webservices.mae.com.ar/APIsMAE

**Características:**
- ✅ API TRD: Registrar operaciones en tiempo real
- ✅ APIs de Back Office: Consulta de operaciones, posiciones, garantías
- ⚠️ Disponible exclusivamente para Agentes MAE
- ⚠️ Enfocado en operaciones, no en datos históricos

**Limitaciones:**
- Solo para agentes registrados
- Enfocado en operaciones, no en análisis histórico

---

### 3. **Primary - Centro de APIs**
**URL:** https://apihub.primary.com.ar/

**Características:**
- ✅ Integración con sistemas de back office bursátil
- ✅ Plataformas de trading
- ✅ Administración de cuentas, movimientos, tenencias
- ✅ Envío de órdenes a mercados con gestión de riesgo
- ⚠️ Requiere cuenta y posiblemente membresía

**Limitaciones:**
- Enfocado en operaciones, no en datos históricos
- Puede requerir membresía

---

### 4. **Banco Central de la República Argentina (BCRA)**
**URL:** https://www.bcra.gob.ar/BCRAyVos/catalogo-de-APIs-banco-central.asp

**Características:**
- ✅ **APIs PÚBLICAS Y GRATUITAS**
- ✅ API de Principales Variables: Variables económicas relevantes
- ✅ API de Estadísticas Cambiarias: Cotizaciones de divisas
- ✅ Sin requerimientos de membresía
- ✅ Datos oficiales y confiables

**Ventajas:**
- Públicas y gratuitas
- Datos oficiales
- Sin restricciones de acceso
- Útiles para análisis macroeconómico

**Limitaciones:**
- No incluye datos de acciones/ONs/bonos individuales
- Enfocado en variables macroeconómicas y divisas

---

### 5. **IOL (invertironline)**
**URL:** https://www.invertironline.com/api

**Características:**
- ✅ API disponible para usuarios de IOL
- ✅ Datos de mercado
- ✅ Seguimiento de portafolios
- ✅ Operaciones
- ✅ Creación de algoritmos de trading
- ✅ **Ya implementada en el bot**

**Ventajas:**
- Ya la estamos usando
- Acceso a datos de mercado argentino
- Soporte para múltiples instrumentos

**Limitaciones:**
- Requiere cuenta IOL
- Datos históricos limitados (principalmente actuales)
- No todos los instrumentos tienen histórico completo

---

### 6. **APIs de Terceros**

#### **MonedAPI**
**URL:** https://monedapi.ar/

**Características:**
- ✅ Cotizaciones de divisas en tiempo real
- ✅ Datos económicos
- ⚠️ Enfocado en divisas, no en acciones

#### **ArgenStats**
**URL:** https://argenstats.com/documentacion

**Características:**
- ✅ Datos económicos
- ✅ Estadísticas argentinas
- ⚠️ No específico para bolsa

---

## 📋 Estado Actual del Bot

### ✅ Lo que ya tenemos:
1. **IOL API**: Implementada y funcionando
   - Obtiene cotizaciones actuales
   - Soporte para múltiples instrumentos
   - Integrada en `IOLClient`

2. **Yahoo Finance**: Implementada y funcionando
   - Datos históricos para acciones argentinas (con sufijo .BA)
   - Funciona bien para acciones principales
   - Implementada en `YahooFinanceClient` y `BYMAClient`

3. **Multi-Source Client**: Implementado
   - Intenta múltiples fuentes en orden de prioridad
   - Fallback automático entre fuentes

### ⚠️ Limitaciones actuales:
1. **Datos históricos para ONs, Bonos, Letras:**
   - Yahoo Finance no tiene datos para estos instrumentos
   - IOL solo proporciona cotizaciones actuales
   - No hay fuente pública de datos históricos completos

2. **APIs de BYMA/MAE:**
   - Requieren membresía y homologación
   - No son accesibles para uso general

---

## 🚀 Recomendaciones de Mejora

### 1. **Mejorar uso de IOL API** (IMPLEMENTADO ✅)
- ✅ Priorizar IOL para instrumentos argentinos específicos
- ✅ Detectar automáticamente ONs, bonos, letras
- ✅ Obtener cotización actual desde IOL

### 2. **Integrar BCRA API** (PENDIENTE)
**Beneficios:**
- Datos macroeconómicos oficiales
- Variables económicas relevantes
- Cotizaciones de divisas
- Gratis y público

**Implementación sugerida:**
```python
class BCRAClient:
    """Cliente para APIs públicas del BCRA"""
    
    def get_currency_rates(self):
        """Obtiene cotizaciones de divisas"""
        # API de Estadísticas Cambiarias
        
    def get_economic_variables(self):
        """Obtiene variables económicas principales"""
        # API de Principales Variables
```

### 3. **Acumular datos históricos desde IOL**
**Estrategia:**
- Guardar cotizaciones diarias obtenidas desde IOL
- Construir base de datos histórica propia
- Usar para análisis cuando no hay datos externos

**Implementación sugerida:**
```python
class HistoricalDataAccumulator:
    """Acumula datos históricos desde múltiples fuentes"""
    
    def save_daily_quote(self, symbol, quote_data):
        """Guarda cotización diaria"""
        
    def get_historical_data(self, symbol, days):
        """Obtiene datos históricos acumulados"""
```

### 4. **Web Scraping de BYMA (último recurso)**
**Consideraciones:**
- Solo para datos públicos
- Respetar términos de servicio
- Usar como último recurso
- Implementar rate limiting

---

## 📊 Prioridad de Implementación

### 🔴 Alta Prioridad:
1. ✅ **Mejorar uso de IOL API** - COMPLETADO
   - Priorizar para instrumentos argentinos
   - Detección automática de tipo de instrumento

### 🟡 Media Prioridad:
2. **Integrar BCRA API**
   - Datos macroeconómicos
   - Variables económicas
   - Mejora análisis fundamental

3. **Acumular datos históricos**
   - Base de datos propia
   - Construcción gradual de histórico

### 🟢 Baja Prioridad:
4. **Web Scraping BYMA**
   - Solo si es absolutamente necesario
   - Respetar términos de servicio
   - Implementar cuidadosamente

---

## 🔧 Código Actual

### Archivos relevantes:
- `src/connectors/iol_client.py` - Cliente IOL (✅ implementado)
- `src/connectors/multi_source_client.py` - Cliente multi-fuente (✅ mejorado)
- `src/connectors/byma_client.py` - Cliente BYMA/Yahoo (✅ implementado)
- `src/connectors/yahoo_client.py` - Cliente Yahoo Finance (✅ implementado)

### Mejoras recientes:
- ✅ IOL ahora es primera fuente para instrumentos argentinos
- ✅ Detección automática de ONs, bonos, letras
- ✅ Obtención de cotización actual desde IOL

---

## 📝 Notas Finales

1. **APIs públicas limitadas:**
   - La mayoría de APIs de bolsa requieren membresía
   - BCRA es la mejor opción pública disponible
   - IOL es la mejor opción para datos de mercado

2. **Datos históricos:**
   - Para acciones: Yahoo Finance funciona bien
   - Para ONs/bonos/letras: Necesitamos acumular datos propios
   - IOL puede ser fuente para acumulación

3. **Recomendación principal:**
   - Continuar usando IOL como fuente principal para instrumentos argentinos
   - Integrar BCRA para datos macroeconómicos
   - Implementar acumulación de datos históricos propios

---

## 🔗 Referencias

- BYMA APIs: https://www.byma.com.ar/byma-apis
- MAE APIs: https://webservices.mae.com.ar/APIsMAE
- Primary APIs: https://apihub.primary.com.ar/
- BCRA APIs: https://www.bcra.gob.ar/BCRAyVos/catalogo-de-APIs-banco-central.asp
- IOL API: https://www.invertironline.com/api
- MonedAPI: https://monedapi.ar/
- ArgenStats: https://argenstats.com/documentacion

