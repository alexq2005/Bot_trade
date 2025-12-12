# 🚀 Guía para Ejecutar Operación Real en IOL

## ⚠️ ADVERTENCIAS IMPORTANTES

- **Este bot operará con DINERO REAL**
- **Las operaciones son IRREVERSIBLES**
- **Asegúrate de haber probado en Paper Trading primero**
- **Revisa la configuración de riesgo antes de ejecutar**

## 📋 Pasos para Ejecutar

### Opción 1: Usando el Script de Prueba

```bash
cd financial_ai/test2_bot_trade
python test_live_trade.py
```

El script:
1. Verificará la conexión con IOL
2. Mostrará el saldo disponible
3. Pedirá confirmación antes de ejecutar
4. Ejecutará UN ciclo de análisis
5. El bot ejecutará compras si encuentra señales BUY

### Opción 2: Usando el Bot Directamente

```bash
cd financial_ai/test2_bot_trade
python trading_bot.py --live
```

Esto ejecutará:
- Un ciclo de análisis
- Operaciones reales si hay señales BUY
- En modo LIVE (dinero real)

### Opción 3: Modo Continuo (Cuidado)

```bash
cd financial_ai/test2_bot_trade
python trading_bot.py --live --continuous --interval 60
```

Esto ejecutará:
- Ciclos continuos cada 60 minutos
- Operaciones reales en cada ciclo
- ⚠️ **Solo usar si estás seguro de la configuración**

## 🔍 Verificación Pre-Ejecución

Antes de ejecutar, verifica:

1. **Conexión IOL**: ✅ Funcionando
2. **Saldo disponible**: Debe ser suficiente
3. **Símbolos configurados**: Revisa qué símbolos se analizarán
4. **Gestión de riesgo**: Verifica límites de posición y stop loss
5. **Configuración de capital**: Asegúrate de que el capital sea correcto

## 📊 Monitoreo Durante la Ejecución

Durante la ejecución, el bot mostrará:

- Análisis de cada símbolo
- Señales generadas (BUY/SELL/HOLD)
- Operaciones ejecutadas
- Resultados del análisis

## 📝 Después de la Ejecución

Revisa:

1. **Archivo `trades.json`**: Ver operaciones ejecutadas
2. **Cuenta IOL**: Confirmar operaciones en la plataforma
3. **Logs del bot**: Revisar detalles de las decisiones
4. **Portafolio**: Ver posiciones abiertas

## 🛑 Detener el Bot

Presiona `Ctrl+C` para detener el bot en cualquier momento.

## ⚙️ Configuración de Símbolos

Por defecto, el bot usa: `['AAPL', 'MSFT', 'GOOGL']`

Para cambiar los símbolos, edita el script o usa:

```python
bot = TradingBot(
    symbols=['GGAL', 'PAMP', 'YPFD'],  # Símbolos argentinos
    paper_trading=False  # LIVE mode
)
```

## 💡 Recomendaciones

1. **Empieza con un ciclo único** (no continuo)
2. **Usa símbolos que conozcas**
3. **Revisa los resultados antes de ejecutar más ciclos**
4. **Monitorea el bot durante la ejecución**
5. **Ten un plan de salida** (stop loss configurado)

## 📞 Soporte

Si encuentras problemas:
- Revisa los logs del bot
- Verifica la conexión con IOL
- Confirma que el saldo es suficiente
- Verifica que los símbolos estén disponibles en IOL

