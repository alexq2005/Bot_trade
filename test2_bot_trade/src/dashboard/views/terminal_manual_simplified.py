import streamlit as st
import time
import logging
from datetime import datetime
from src.services.price_service import PriceService
from src.services.price_service import PriceService
from src.services.trading_form_service import TradingFormService
from src.services.portfolio_persistence import load_portfolio

logger = logging.getLogger(__name__)

def render_manual_trading_simplified():
    """
    Renderiza la interfaz de trading manual optimizada.
    Evita reruns innecesarios y usa una gestión de estado limpia.
    """
    st.subheader("💼 Trading Manual Directo")
    
    # 1. Configuración e Inicialización
    if 'iol_client' not in st.session_state or not st.session_state.iol_client:
        st.error("❌ Conexión a IOL no disponible.")
        return

    iol_client = st.session_state.iol_client
    
    # Servicios en Session State (Singleton pattern)
    if 'price_service' not in st.session_state:
        st.session_state.price_service = PriceService(iol_client)
    if 'trading_form_service' not in st.session_state:
        st.session_state.trading_form_service = TradingFormService(iol_client, st.session_state.price_service)
        
    price_service = st.session_state.price_service
    form_service = st.session_state.trading_form_service

    # 2. Selección de Activo
    col_sel, col_bal = st.columns([2, 1])
    
    with col_sel:
        # Cargar lista de activos
        portfolio = load_portfolio()
        my_symbols = [item['symbol'] for item in portfolio] if portfolio else []
        default_symbols = sorted(list(set(my_symbols + ['GGAL.BA', 'YPFD.BA', 'AL30.BA', 'GD30.BA', 'SPY', 'AAPL', 'MSFT'])))
        
        def on_symbol_change():
            # Callback: se ejecuta ANTES del re-render
            new_symbol = st.session_state.tm_symbol_select_v2
            # Limpiar cache del nuevo símbolo para asegurar precio fresco
            st.session_state.price_service.clear_cache(new_symbol)
            # Limpiar input de precio limite anterior
            if f"tm_limit_price_{new_symbol}" in st.session_state:
                del st.session_state[f"tm_limit_price_{new_symbol}"]

        # Selectbox con callback explícito y KEY NUEVA para resetear estado
        selected_symbol = st.selectbox(
            "Seleccionar Activo", 
            default_symbols,
            key="tm_symbol_select_v2",
            on_change=on_symbol_change
        )
        
        # DEBUG VISUAL DIRECTO
        st.caption(f"🔍 DEBUG INTERNO: Widget='{selected_symbol}'")



    with col_bal:
        # Saldo (con cache simple en el servicio si fuera necesario, aqui directo)
        try:
            balance = form_service.get_available_balance()
            st.metric("Saldo Disponible", f"${balance:,.2f}")
        except:
            st.metric("Saldo Disponible", "Error")

    st.markdown("---")

    # 3. Precio en Tiempo Real
    # Obtener precio (el servicio maneja el cache de 10s por defecto)
    col_price, col_refresh = st.columns([3, 1])
    
    with col_price:
        # FORCE RELOAD - Getting price
        current_price = price_service.get_price(selected_symbol)
        
        if current_price:
            timestamp_str = datetime.now().strftime("%H:%M:%S")
            # Note: 'key' parameter removed - not supported in current Streamlit version
            # Price updates are handled by cache invalidation in PriceService
            
            st.metric(
                label=f"Precio Actual {selected_symbol}",
                value=f"${current_price:,.2f}",
                delta=f"🕒 {timestamp_str}",
                delta_color="off"  # Grey color for time
            )
        else:
            st.warning(f"⚠️ Precio no disponible para {selected_symbol}")
            
    with col_refresh:
        # Botón manual de refresh
        if st.button("🔄 Actualizar", key="tm_refresh_btn"):
            price_service.clear_cache(selected_symbol)
            st.rerun()

    # 4. Formulario de Orden
    st.markdown("### 📝 Nueva Orden")
    
    with st.form(key=f"order_form_{selected_symbol}"): # Key única por símbolo limpia el formulario al cambiar
        c1, c2 = st.columns(2)
        
        with c1:
            side = st.radio("Operación", ["COMPRA", "VENTA"], horizontal=True)
            quantity = st.number_input("Cantidad", min_value=1, step=1, value=1)
            
        with c2:
            order_type = st.radio("Tipo de Precio", ["Mercado", "Límite"], horizontal=True)
            
            # Lógica de precio para el input
            default_price_val = current_price if current_price else 0.0
            
            if order_type == "Límite":
                limit_price = st.number_input(
                    "Precio Límite", 
                    value=default_price_val,
                    min_value=0.0, 
                    step=0.5,
                    format="%.2f"
                )
            else:
                st.info(f"Ejecución a mercado (~${default_price_val:,.2f})")
                limit_price = 0.0 # Mercado

        # Cálculos estimados (fuera del form submit para reactividad, pero dentro de form requiere submit)
        # En Streamlit forms, no hay reactividad inmediata. Para reactividad, sacar del st.form.
        # Usuario pidió optimización -> Saquemos los cálculos fuera para que sean reactivos sin rerun loop.
        
        submit = st.form_submit_button("🚀 Enviar Orden", type="primary")

    if submit:
        # Validación y Ejecución
        is_market = (order_type == "Mercado")
        price_to_use = limit_price if not is_market else (current_price if current_price else 0.0)
        
        if price_to_use <= 0:
            st.error("❌ Precio inválido")
        else:
            with st.spinner("Enviando orden..."):
                result = form_service.execute_order(
                    symbol=selected_symbol,
                    side="buy" if side == "COMPRA" else "sell",
                    quantity=quantity,
                    price=limit_price, # Si es mercado, el servicio lo maneja (envía 0 o lo que requiera IOL)
                    is_market_order=is_market
                )
                
                if result.get("success"):
                    st.success(f"✅ Orden Enviada: {result.get('message', 'OK')}")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ Error: {result.get('error')}")

