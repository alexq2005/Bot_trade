# 📋 Guía de Revisión del Pull Request de Jules

## Paso 1: Ver el Pull Request en GitHub

1. Ve a: <https://github.com/alexq2005/Bot_trade/pulls>
2. Busca el PR de Jules (probablemente se llame "Audit fixes" o similar)
3. Revisa la descripción y los archivos cambiados

## Paso 2: Revisar los Cambios (Diff)

**Archivos que Jules probablemente modificó:**

- `test2_bot_trade/trading_bot.py` (comentó 2 líneas de debug)
- Posiblemente otros archivos menores

**Qué buscar:**

- ✅ Solo cambios menores (comentarios, imports)
- ❌ Cambios masivos en lógica de negocio (SOSPECHOSO)
- ❌ Eliminación de archivos importantes (PELIGROSO)

## Paso 3: Descargar y Probar Localmente

```bash
# Opción A: Merge directo desde GitHub (si confías 100%)
# Click en "Merge Pull Request" en la web

# Opción B: Probar localmente primero (RECOMENDADO)
git fetch origin
git checkout -b review-jules origin/[nombre-rama-de-jules]

# Ejecutar validación
python scripts/validate_post_merge.py

# Si pasa, probar dashboard
streamlit run test2_bot_trade/dashboard.py

# Si todo funciona:
git checkout main
git merge review-jules
git push origin main
```

## Paso 4: Post-Merge

- [ ] Ejecutar `python scripts/validate_post_merge.py`
- [ ] Abrir Dashboard y navegar 3 pestañas
- [ ] Verificar que Terminal de Trading cargue precios
- [ ] Confirmar que no hay errores en consola

## 🚨 Si Algo Sale Mal

```bash
# Revertir el merge
git reset --hard HEAD~1
git push origin main --force

# O crear un revert commit (más seguro)
git revert HEAD
git push origin main
```

---

**Consejo:** Si tienes dudas, pídeme que revise el diff antes de hacer merge.
