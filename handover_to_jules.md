# 🦅 PROTOCOLO DE AUDITORÍA TOTAL: IOL Quantum AI

**Para:** Jules (AI Developer)
**Prioridad:** CRÍTICA
**Objetivo:** Identificar y eliminar EL 100% DE LOS ERRORES (Conocidos y Ocultos).

Jules, tu primera misión no es escribir código nuevo, es **AUDITAR** lo existente. El usuario reporta inestabilidad. Ejecuta este protocolo paso a paso.

---

## 🔍 FASE 1: Detección de Errores Estáticos (Static Analysis)

*Ejecutar inmediatamente al recibir el proyecto.*

1. **Escaneo de Sintaxis y Tipos:**
    * Ejecuta: `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
    * *Objetivo:* Encontrar errores de sintaxis (E9), variables indefinidas (F82) y tests de igualdad inválidos (F63).
2. **Detección de Importaciones Circulares:**
    * Analiza los módulos `src/services` y `src/dashboard`.
    * *Síntoma a buscar:* `ImportError: cannot import name ... from partially initialized module`.
    * *Acción:* Mapear las dependencias cruzadas.
3. **Validación de Configuración (`.env` vs `config.py`):**
    * Verifica que TODAS las variables usadas en `config.py` tengan un valor real en el entorno. No permitas `None` silenciosos.

---

## 🧪 FASE 2: Pruebas de Humo (Smoke Tests)

*Ejecutar scripts para forzar fallos en tiempo de ejecución.*

1. **Dashboard "Dry Run":**
    * Comando: `streamlit run dashboard.py` (debe arrancar sin excepciones en consola por 60 segundos).
2. **Entrenamiento ML Simulado:**
    * Comando: `python scripts/train_model.py --dry-run --epochs 1`
    * *Objetivo:* Verificar que no falten librerías (`ModuleNotFoundError`) y que los datos fluyan por la red neuronal sin errores de dimensiones (`ValueError: Shape mismatch`).
3. **Conector IOL (Prueba de Vida):**
    * Comando: Crear y ejecutar `scripts/test_connection.py` que haga un simple `iol_client.get_account_status()`.
    * *Criterio:* Debe devolver JSON válido, no crashear por Token Expirado.

---

## 🐛 FASE 3: Auditoría de Lógica de Negocio

1. **Revisión de "Trading Manual" (`terminal_manual_simplified.py`):**
    * Confirma que la corrección de `PriceService` (uso de `st.session_state` y invalidación de caché) se mantenga intacta.
2. **Bot Autonomo (`bot.py` / `watchdog.py`):**
    * Revisar la lógica de *Rate Limiting*. ¿Estamos respetando los límites de la API de IOL o nos van a banear?
3. **Persistencia de Portfolio:**
    * Verificar si `portfolio.json` se recupera automáticamente si está corrupto (vacío o JSON inválido).

---

## 📝 REPORTE DE ERRORES

Genera un archivo `AUDIT_REPORT.md` con:

* [ ] Lista de Archivos con Errores de Sintaxis.
* [ ] Lista de Librerías Faltantes en `requirements.txt`.
* [ ] Vulnerabilidades de Seguridad (Tokens expuestos).
* [ ] Funcionalidades Rotas (Botones que no hacen nada).

**Instrucción Final para Jules:** No asumas que nada funciona. VERIFICA TODO.
