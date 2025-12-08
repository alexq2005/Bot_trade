# 🚀 IOL Quantum AI Trading System

Sistema de trading algorítmico avanzado con inteligencia artificial, análisis técnico, y optimización de portafolio.

## 📊 Características Principales

### ✅ Implementado

- **Base de Datos**: SQLite con 1,247+ registros históricos
- **Predicción con IA**: Modelo LSTM (TensorFlow/Keras)
- **Análisis Técnico**: RSI, MACD, Bollinger Bands, ATR, ADX, Stochastic
- **Optimización de Portafolio**: Markowitz, Min Variance, Risk Parity
- **Backtesting Engine**: Prueba de estrategias en datos históricos
- **Risk Management**: Stop-loss, take-profit, position sizing, Kelly Criterion
- **Dashboard Web**: Interfaz interactiva con Streamlit
- **CLI Principal**: Interfaz de línea de comandos para gestión completa
- **Sistema de Logging**: Logging centralizado con colores y archivos rotativos
- **Health Checks**: Verificación automática del estado del sistema
- **Configuración Centralizada**: Gestión unificada de configuración
- **Utilidades**: Funciones helper para operaciones comunes

### 🔄 En Desarrollo

- Conexión IOL API (requiere activación de cuenta)
- Sistema de alertas en tiempo real
- Ejecución automática de órdenes

## 🛠️ Instalación

### Requisitos

- Python 3.10+
- pip

### Setup

```bash
# Clonar repositorio
cd financial_ai

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciales
cp .env.example .env
# Editar .env con tus credenciales
```

## 🚀 Uso

### CLI Principal (Recomendado)

El proyecto ahora incluye un CLI principal para gestionar todas las operaciones:

```bash
# Verificar estado del sistema
python cli.py health

# Mostrar configuración
python cli.py config show

# Iniciar bot en modo paper trading
python cli.py bot start

# Iniciar bot en modo live (requiere confirmación)
python cli.py bot start --live

# Entrenar modelo
python cli.py train --symbol AAPL --epochs 30

# Iniciar dashboard
python cli.py dashboard

# Ejecutar pruebas extremas
python cli.py test --extreme

# Ver ayuda completa
python cli.py --help
```

### Uso Tradicional

#### 1. Ingestar Datos Históricos

```bash
python scripts/ingest_data.py
# O usando CLI:
python cli.py data ingest
```

#### 2. Entrenar Modelo LSTM

```bash
# Entrenar para un símbolo específico
python scripts/train_model.py --symbol AAPL --epochs 30
# O usando CLI:
python cli.py train --symbol AAPL --epochs 30

# Entrenar todos los símbolos
python cli.py train --all
```

#### 3. Ejecutar Backtesting

```bash
python scripts/test_backtest.py
```

#### 4. Lanzar Dashboard

```bash
streamlit run dashboard.py
# O usando CLI:
python cli.py dashboard
```

El dashboard estará disponible en `http://localhost:8501`

## 📈 Módulos del Sistema

### 1. Data Layer (`src/core/`)

- `database.py`: Configuración SQLAlchemy
- `config.py`: Gestión de configuración

### 2. Connectors (`src/connectors/`)

- `yahoo_client.py`: Cliente Yahoo Finance (activo)
- `iol_client.py`: Cliente IOL (pendiente activación)

### 3. Models (`src/models/`)

- `market_data.py`: Modelo de datos de mercado
- `price_predictor.py`: Modelo LSTM para predicción

### 4. Services (`src/services/`)

- `prediction_service.py`: Servicio de predicciones
- `technical_analysis.py`: Análisis técnico
- `portfolio_optimizer.py`: Optimización de portafolio
- `backtester.py`: Motor de backtesting
- `risk_manager.py`: Gestión de riesgo

### 5. Scripts (`scripts/`)

- `ingest_data.py`: Ingesta de datos históricos
- `train_model.py`: Entrenamiento de modelos
- `test_predictions.py`: Prueba de predicciones
- `test_technical_analysis.py`: Prueba de análisis técnico
- `test_portfolio.py`: Prueba de optimización
- `test_backtest.py`: Prueba de backtesting

## 📊 Dashboard

El dashboard incluye 5 secciones principales:

1. **📊 Market Overview**
   - Gráficos de velas japonesas
   - Volumen de trading
   - Métricas en tiempo real

2. **🤖 AI Predictions**
   - Predicciones LSTM
   - Señales BUY/SELL/HOLD
   - Nivel de confianza

3. **📈 Technical Analysis**
   - Indicadores de volatilidad (ATR, Bollinger Bands)
   - Indicadores de momentum (RSI, MACD, Stochastic)
   - Indicadores de tendencia (SMA, EMA, ADX)

4. **💼 Portfolio Optimization**
   - Estrategia Max Sharpe Ratio
   - Estrategia Min Variance
   - Estrategia Risk Parity

5. **🎯 Trading Signals**
   - Tabla consolidada de señales
   - Comparación AI vs Técnico
   - Resumen de señales

## 🧪 Resultados de Backtesting

### Estrategia MA Crossover (20/50) - AAPL

- **Capital Inicial**: $10,000
- **Valor Final**: $10,405.97
- **Retorno Total**: 4.06%
- **Sharpe Ratio**: 1.05
- **Max Drawdown**: -3.86%
- **Total Trades**: 5

## 📊 Resultados de Optimización

### Portfolio: AAPL, MSFT, GOOGL, SPY

**Max Sharpe Ratio (Markowitz)**

- Retorno Esperado: 70.50%
- Volatilidad: 33.38%
- Sharpe Ratio: 2.05
- Asignación: 100% GOOGL

**Minimum Variance**

- Retorno Esperado: 16.22%
- Volatilidad: 19.65%
- Sharpe Ratio: 0.72
- Asignación: 85% SPY, 15% MSFT

**Risk Parity**

- Retorno Esperado: 31.68%
- Volatilidad: 22.75%
- Sharpe Ratio: 1.30
- Asignación: 25% cada activo

## 🛡️ Risk Management

El sistema incluye:

- **Position Sizing**: Máximo 10% del portafolio por posición
- **Portfolio Risk**: Máximo 2% de riesgo por trade
- **Stop Loss**: Calculado con ATR (2x multiplier)
- **Take Profit**: Risk-Reward ratio 2:1
- **Kelly Criterion**: Cálculo de tamaño óptimo de posición

## 📝 Comandos Útiles

### CLI Principal

```bash
# Health Checks
python cli.py health                    # Verificar estado del sistema
python cli.py health --json            # Salida en JSON

# Configuración
python cli.py config show              # Mostrar configuración
python cli.py config set app.debug true # Establecer configuración
python cli.py config reload            # Recargar configuración

# Bot de Trading
python cli.py bot start                # Iniciar bot (paper trading)
python cli.py bot start --live        # Iniciar bot (live trading)
python cli.py bot status              # Estado del bot
python cli.py bot stop                # Detener bot

# Entrenamiento
python cli.py train --symbol AAPL     # Entrenar modelo específico
python cli.py train --all             # Entrenar todos los modelos

# Dashboard
python cli.py dashboard                # Iniciar dashboard

# Pruebas
python cli.py test --extreme           # Pruebas extremas
python cli.py test --extreme --full    # Pruebas completas

# Datos
python cli.py data ingest              # Ingerir datos
python cli.py data update              # Actualizar datos
python cli.py data verify              # Verificar datos
```

### Scripts Tradicionales

```bash
# Actualizar datos
python scripts/ingest_data.py

# Verificar base de datos
python scripts/verify_db.py

# Generar predicciones
python scripts/test_predictions.py

# Análisis técnico
python scripts/test_technical_analysis.py

# Optimización de portafolio
python scripts/test_portfolio.py

# Backtesting
python scripts/test_backtest.py

# Organizar archivos del proyecto
python scripts/organize_files.py --execute
```

## 🆕 Nuevas Funcionalidades

### Sistema de Logging

El proyecto ahora incluye un sistema de logging centralizado:

```python
from src.core.logger import get_logger

logger = get_logger("mi_modulo")
logger.info("Mensaje informativo")
logger.error("Mensaje de error")
```

Los logs se guardan en:
- `logs/trading_bot_YYYYMMDD.log` - Logs generales
- `logs/errors_YYYYMMDD.log` - Solo errores

### Health Checks

Verifica el estado de todos los componentes:

```bash
python cli.py health
```

Verifica:
- ✅ Base de datos
- ✅ Modelos entrenados
- ✅ Espacio en disco
- ✅ Sistema de logs
- ✅ Configuración
- ✅ Conexión IOL

### Configuración Centralizada

Toda la configuración se gestiona desde un solo lugar:

```python
from src.core.config_manager import get_config, set_config

# Obtener configuración
debug = get_config('app.debug')
capital = get_config('trading.initial_capital')

# Establecer configuración
set_config('app.debug', True)
```

### Utilidades del Proyecto

Funciones helper disponibles:

```python
from src.utils import (
    format_currency,
    format_percentage,
    get_project_root,
    backup_file,
    validate_symbol,
)
```

## 🗂️ Estructura del Proyecto Mejorada

```
financial_ai/
├── cli.py                 # CLI principal (NUEVO)
├── config/                # Configuración centralizada (NUEVO)
│   └── app_config.json
├── logs/                   # Logs del sistema (NUEVO)
├── data/                   # Datos del proyecto (NUEVO)
│   ├── databases/
│   ├── html/
│   └── json/
├── assets/                 # Recursos (NUEVO)
│   └── images/
├── docs/                   # Documentación (NUEVO)
├── src/
│   ├── core/
│   │   ├── logger.py      # Sistema de logging (NUEVO)
│   │   ├── config_manager.py  # Gestor de configuración (NUEVO)
│   │   └── health_check.py    # Health checks (NUEVO)
│   └── utils/             # Utilidades (NUEVO)
│       └── project_utils.py
├── scripts/
│   ├── organize_files.py   # Organizar archivos (NUEVO)
│   └── ...
└── ...
```

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# IOL Credentials
IOL_USERNAME=your_username
IOL_PASSWORD=your_password

# API URLs
IOL_API_URL=https://api.iol.invertironline.com/api
IOL_TOKEN_URL=https://api.iol.invertironline.com/token

# App Settings
APP_ENV=development
DEBUG=True
```

## 📚 Tecnologías Utilizadas

- **Python 3.10+**
- **TensorFlow/Keras**: Modelos LSTM
- **SQLAlchemy**: ORM para base de datos
- **Pandas**: Manipulación de datos
- **NumPy**: Cálculos numéricos
- **SciPy**: Optimización
- **Streamlit**: Dashboard web
- **Plotly**: Visualizaciones interactivas
- **yfinance**: Datos de mercado
- **ta**: Indicadores técnicos

## 🎯 Próximos Pasos

1. **Activar IOL API** - Habilitar trading real
2. **Sistema de Alertas** - Notificaciones automáticas (email, SMS)
3. **Continuous Learning** - Reentrenamiento automático de modelos
4. **Advanced Execution** - Algoritmos VWAP, TWAP
5. **Multi-timeframe Analysis** - Análisis en múltiples marcos temporales

## 📄 Licencia

Este proyecto es de uso personal y educativo.

## 👤 Autor

Sistema desarrollado siguiendo las especificaciones del documento "Sistema de Trading Algorítmico IOL Quantum AI".

---

**⚠️ Disclaimer**: Este sistema es para fines educativos y de investigación. El trading algorítmico conlleva riesgos significativos. Siempre realiza tu propia investigación y consulta con profesionales financieros antes de operar con dinero real.
