# 💬 CHAT INTERACTIVO CON EL BOT

## 🎯 CARACTERÍSTICAS

El bot ahora tiene un sistema de chat interactivo que permite:

- ✅ **Comunicación espontánea** - El bot razona y responde de forma natural
- ✅ **Acceso a internet** - Puede buscar información en tiempo real
- ✅ **Aprendizaje basado en intereses** - Aprende de las conversaciones
- ✅ **Mejora autónoma** - Se mejora basado en sus intereses

---

## 🚀 USO

### Modo Consola (Interactivo)

```bash
cd test2_bot_trade
python chat_bot.py
```

Esto iniciará una conversación interactiva donde puedes:

- Conversar con el bot de forma natural
- Hacer preguntas sobre trading
- Pedirle que busque información
- Ver su estado y pensamientos
- Obtener sugerencias de mejora

### Comandos Especiales

- `estado` - Muestra el estado actual del bot, sus intereses y pensamientos
- `mejoras` - Muestra sugerencias de mejora basadas en intereses
- `salir` - Termina la conversación

---

## 💡 EJEMPLOS DE CONVERSACIÓN

### Ejemplo 1: Pregunta Simple

```
Tú: ¿Cómo está mi win rate?

Bot: Mi win rate actual depende de mis trades recientes. Puedo analizarlo si quieres. 
     ¿Te interesa ver mis métricas?

💭 Me pregunto sobre win rate...
```

### Ejemplo 2: Búsqueda de Información

```
Tú: Busca información sobre estrategias de trading para mercados volátiles

Bot: 🔍 Buscando información: estrategias trading mercados volátiles

Encontré información sobre 'estrategias trading mercados volátiles':

1. Estrategias para Mercados Volátiles
   Los mercados volátiles requieren estrategias específicas como...

2. Trading en Alta Volatilidad
   Cuando la volatilidad es alta, es importante...

Esto es interesante. ¿Te gustaría que investigue más sobre algún aspecto específico?
```

### Ejemplo 3: Conversación Espontánea

```
Tú: ¿Qué opinas sobre el mercado actual?

Bot: Eso es muy interesante. Déjame pensar en eso... Por cierto, he estado 
     pensando mucho sobre win rate últimamente.

💭 ¿Cómo puedo mejorar mi win rate?
```

---

## 🧠 RAZONAMIENTO ESPONTÁNEO

El bot puede generar pensamientos espontáneos basados en:

- **Intereses actuales** - Sobre qué está pensando
- **Performance** - Cómo puede mejorar
- **Conversaciones** - Qué ha aprendido

Estos pensamientos aparecen ocasionalmente durante la conversación.

---

## 🔍 BÚSQUEDA EN INTERNET

El bot puede buscar información cuando detecta que la necesitas:

- Palabras clave: "buscar", "investigar", "información", "noticias", "actual"
- Búsquedas automáticas sobre temas de trading
- Resultados relevantes y contextualizados

### Configuración de Búsqueda

Por defecto usa **DuckDuckGo** (gratis, sin API key).

Para mejor funcionalidad, instala:
```bash
pip install duckduckgo-search
```

Opcionalmente puedes configurar Google Custom Search API (requiere API key).

---

## 📚 APRENDIZAJE BASADO EN INTERESES

El bot aprende de las conversaciones:

### Intereses

- Detecta temas de conversación
- Prioriza temas frecuentes
- Aprende qué te interesa

### Mejoras Sugeridas

Basado en intereses, el bot puede sugerir:

- Optimización de umbrales si hablas de win rate
- Evaluación de estrategias si hablas de estrategias
- Ajuste de riesgo si hablas de gestión de riesgo

### Memoria

El bot guarda:

- Conversaciones recientes
- Experiencias y aprendizajes
- Conocimiento adquirido

Archivos:
- `data/agent_memory.json` - Memoria del agente
- `data/agent_interests.json` - Intereses y prioridades
- `data/conversation_history.json` - Historial de conversaciones

---

## 🔗 INTEGRACIÓN CON TELEGRAM

El chat también funciona por Telegram si está configurado.

El bot responderá automáticamente a mensajes de Telegram usando el mismo sistema de razonamiento.

---

## 🎨 PERSONALIDAD DEL BOT

El bot tiene una personalidad configurable:

- **Curiosidad:** 0.8 (muy curioso)
- **Creatividad:** 0.7 (creativo)
- **Velocidad de aprendizaje:** 0.6 (aprende rápido)
- **Espontaneidad:** 0.75 (bastante espontáneo)

Estos valores afectan cómo razona y responde.

---

## 📊 COMANDOS ÚTILES

### Ver Estado del Bot

```
Tú: estado

Bot: 🤖 Estado del Bot:

Intereses actuales:
1. win rate
2. estrategias
3. riesgo

Pensamientos recientes:
• Me pregunto sobre win rate...
• ¿Cómo puedo mejorar mi win rate?
```

### Ver Sugerencias de Mejora

```
Tú: mejoras

Bot: 💡 Sugerencias de mejora basadas en mis intereses:

• win rate: Analizar y optimizar umbrales de entrada (Prioridad: high)
• estrategias: Evaluar performance de estrategias individuales (Prioridad: medium)
```

---

## 🔄 MEJORA AUTÓNOMA BASADA EN INTERESES

El bot puede mejorar basado en sus intereses:

1. **Detecta intereses** de las conversaciones
2. **Prioriza mejoras** según intereses
3. **Sugiere cambios** específicos
4. **Aplica mejoras** si se le solicita

---

## ⚙️ CONFIGURACIÓN

### Personalidad

Puedes ajustar la personalidad en `src/services/advanced_reasoning_agent.py`:

```python
self.personality = {
    'curiosity': 0.8,      # Nivel de curiosidad (0-1)
    'creativity': 0.7,      # Nivel de creatividad
    'learning_rate': 0.6,   # Velocidad de aprendizaje
    'spontaneity': 0.75     # Nivel de espontaneidad
}
```

### Motor de Búsqueda

En `src/services/web_search_agent.py`:

```python
self.search_engine = 'duckduckgo'  # o 'google'
self.api_key = None  # Para Google Custom Search
```

---

## 🎯 CASOS DE USO

### 1. Consulta de Performance

```
Tú: ¿Cómo van mis trades?

Bot: Puedo analizar tus trades recientes. Déjame revisar...
     [Analiza y responde con métricas]
```

### 2. Búsqueda de Información

```
Tú: Busca noticias sobre el mercado argentino

Bot: 🔍 Buscando información...
     [Muestra resultados relevantes]
```

### 3. Discusión de Estrategias

```
Tú: ¿Qué estrategias están funcionando mejor?

Bot: Basado en mi análisis, las estrategias X, Y y Z tienen mejor performance...
     [Explica y razona]
```

### 4. Mejora Autónoma

```
Tú: ¿Puedes mejorarte?

Bot: Claro, basado en mis intereses actuales, puedo:
     - Optimizar umbrales de entrada
     - Ajustar stop loss
     - Evaluar estrategias
     
     ¿Quieres que ejecute estas mejoras?
```

---

## 📝 NOTAS

- El bot aprende de cada conversación
- Sus intereses evolucionan con el tiempo
- Puede generar pensamientos espontáneos
- Las búsquedas web requieren conexión a internet
- Todo se guarda en `data/` para persistencia

---

## 🚨 ADVERTENCIAS

- El bot puede modificar su comportamiento basado en intereses
- Las búsquedas web pueden no ser siempre precisas
- El razonamiento es probabilístico, no determinístico
- Monitorea las mejoras que el bot sugiere

---

**¡Disfruta conversando con tu bot inteligente!** 💬🤖

