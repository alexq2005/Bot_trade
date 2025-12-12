import streamlit as st
import sys
import logging
import warnings
import os

# Import utility classes and functions
from src.dashboard.utils import (
    SafeStderr, 
    SafeLogHandler, 
    initialize_iol_client
)
from src.dashboard.components.styles import apply_custom_styles
from src.dashboard.components.sidebar import render_sidebar
from src.dashboard.watchdog import get_telegram_watchdog

# --- Global Configuration ---

# Safe Stderr Wrapper
try:
    if sys.stderr.closed or not hasattr(sys.stderr, 'write'):
        sys.stderr = SafeStderr()
except:
    sys.stderr = SafeStderr()

# Logging Configuration
logging.getLogger().setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

# Configure safe logging handlers
for logger_name in ['', 'streamlit', 'streamlit.runtime']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    for handler in logger.handlers[:]:
        try:
             # Basic handler cleanup if needed, or just leave it since we set level to CRITICAL
             pass
        except:
             pass
    # Add safe handler if needed
    try:
        logger.addHandler(SafeLogHandler())
    except:
        pass

# Streamlit Page Config
st.set_page_config(
    page_title="IOL Quantum AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialization ---

# Initialize Telegram Watchdog
if os.getenv("TELEGRAM_BOT_TOKEN"):
    try:
        watchdog = get_telegram_watchdog()
        if not watchdog.running:
            watchdog.start()
    except Exception as e:
        print(f"⚠️ Error iniciando watchdog: {e}")

# Apply Custom Styles
apply_custom_styles()

# Initialize IOL Client (Auto-connect)
if 'iol_client' not in st.session_state:
    initialize_iol_client()

# Initialize navigation state BEFORE rendering sidebar (to avoid widget modification error)
if 'main_navigation' not in st.session_state:
    st.session_state.main_navigation = "🖥️ Command Center"

# --- Main Layout ---

# Render Sidebar and get current page
current_page = render_sidebar()

# --- Page Routing ---

if current_page == "Command Center":
    from src.dashboard.views.command_center import render
    render()

elif current_page == "🏠 Inicio":
    from src.dashboard.views.home import render
    render()

elif current_page == "💼 Gestión de Activos":
    from src.dashboard.views.assets_management import render
    render()

elif current_page == "🤖 Bot Autónomo":
    from src.dashboard.views.trading_bot import render
    try:
        render()
    except Exception as e:
        st.error(f"Error en Bot Autónomo: {e}")

elif current_page == "Genetic Optimizer":
    from src.dashboard.views.genetic_optimizer import render
    render()

elif current_page == "Neural Network":
    from src.dashboard.views.neural_network import render
    render()

elif current_page == "🧬 Estrategias Avanzadas":
    from src.dashboard.views.strategy_optimizer import render
    render()

elif current_page == "⚙️ Sistema & Configuración":
    from src.dashboard.views.system_config import render
    render()

elif current_page == "⚡ Terminal de Trading":
    from src.dashboard.views.terminal import render
    render()

elif current_page == "💬 Chat con el Bot":
    from src.dashboard.views.chat import render
    render()

elif current_page == "📊 Operaciones en Tiempo Real":
    from src.dashboard.views.live_monitor import render
    render()

# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>🚀 IOL Quantum AI | Sistema de Aprendizaje Continuo</div>", unsafe_allow_html=True)
