# 🧪 FASE 2: Guía de Pruebas de Humo (Smoke Tests)

Esta fase verifica que el sistema "arranque" y respire sin colapsar.

## 1. Ejecución Automática

He preparado un script que valida automáticamente imports, entorno y dependencias.

```bash
# Desde la raíz del proyecto
python scripts/verify_phase_2.py
```

**Si este script falla:** DETENTE. No tiene sentido auditar lógica si el sistema no puede ni importar sus propias librerías.

## 2. Pruebas Manuales "Dry Run"

Una vez que `verify_phase_2.py` pase en verde, ejecuta esto:

### A. Dashboard

```bash
streamlit run dashboard.py
```

* **Verificar:** Carga la página de inicio.
* **Acción:** Navega a 3 pestañas diferentes.
* **Criterio:** No debe aparecer el error "StreamlitAPIException" ni pantallas en blanco.

### B. Entrenamiento ML (Simulado)

```bash
python scripts/train_model.py --dry-run
```

* (Si el flag `--dry-run` no está implementado en `train_model.py` todavía, Jules debe implementarlo para que corra 1 sola época con pocos datos).

---
**Resultado Esperado:** Consola limpia de Tracebacks rojos.
