import streamlit as st
from datetime import datetime
from src.dashboard.utils import (
    initialize_iol_client, 
    get_services, 
    get_monitored_symbols, 
    check_bot_status
)
from src.connectors.iol_client import IOLClient
from src.services.portfolio_persistence import load_portfolio

def render_sidebar():
    """Renderiza la barra lateral y devuelve la página seleccionada"""
    services = get_services()
    
    # Enhanced Sidebar Header
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1 style="font-size: 2rem; font-weight: 800; color: white; margin: 0;">
            🚀 IOL Quantum AI
        </h1>
        <p style="color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0.5rem 0;">
            Sistema de Trading Inteligente
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # IOL User Info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 Usuario IOL")
    
    # Mostrar estado de conexión
    if st.session_state.get('iol_client'):
        try:
            # Verificar que la conexión sigue activa
            st.session_state.iol_client.get_account_status()
            connection_status = "🟢 Conectado"
            connection_color = "#4caf50"
        except Exception:
            # Intentar reconectar automáticamente
            if initialize_iol_client():
                connection_status = "🟢 Reconectado"
                connection_color = "#4caf50"
            else:
                connection_status = "🔴 Desconectado"
                connection_color = "#f44336"
    else:
        # Intentar conectar automáticamente
        if initialize_iol_client():
            connection_status = "🟢 Conectado"
            connection_color = "#4caf50"
        else:
            connection_status = "🔴 Sin conexión"
            connection_color = "#f44336"
    
    # Mostrar estado de conexión (Visual)
    st.sidebar.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 0.5rem; border-radius: 8px; margin: 0.5rem 0; text-align: center;">
        <div style="color: {connection_color}; font-weight: 600; font-size: 0.9rem;">{connection_status}</div>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        if st.session_state.get('iol_client'):
            iol_username = st.session_state.iol_client.username
            
            # Try to get account info for more details
            account_info = None
            account_number = None
            try:
                account_status = st.session_state.iol_client.get_account_status()
                if "error" not in account_status and "cuentas" in account_status:
                    if len(account_status["cuentas"]) > 0:
                        account_number = account_status["cuentas"][0].get("numero", "N/A")
                        account_type = account_status["cuentas"][0].get("tipo", "N/A")
                        account_info = {
                            "numero": account_number,
                            "tipo": account_type,
                            "estado": account_status["cuentas"][0].get("estado", "N/A")
                        }
            except Exception:
                pass
            
            # Display user info using Streamlit components (simplified)
            with st.sidebar.container():
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.15); padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="font-size: 1.5rem;">👤</span>
                        <div>
                            <div style="font-weight: 700; color: white; font-size: 1rem;">{iol_username}</div>
                            <div style="font-size: 0.75rem; color: rgba(255,255,255,0.7);">Conectado a IOL</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display account info using Streamlit components (no HTML)
            if account_info:
                st.sidebar.markdown("---")
                st.sidebar.markdown("**📋 Información de Cuenta**")
                st.sidebar.text(f"Cuenta: {account_number}")
                account_type_display = account_info.get('tipo', 'N/A').replace('_', ' ').title()
                st.sidebar.text(f"Tipo: {account_type_display}")
                estado = account_info.get('estado', 'N/A').title()
                estado_emoji = "🟢" if estado.lower() == 'operable' else "🟡"
                st.sidebar.text(f"Estado: {estado_emoji} {estado}")
        else:
            # Si no hay cliente, intentar conectar automáticamente
            if initialize_iol_client():
                st.sidebar.success("✅ Reconectado a IOL automáticamente")
                st.rerun()
            else:
                error_msg = st.session_state.get('iol_connection_error', 'Error desconocido')
                st.sidebar.warning(f"⚠️ No conectado a IOL")
                st.sidebar.info("💡 El dashboard intentará reconectar automáticamente")
                if st.sidebar.button("🔄 Reconectar Ahora", width='stretch'):
                    if initialize_iol_client():
                        st.sidebar.success("✅ Reconectado exitosamente")
                        st.rerun()
                    else:
                        st.sidebar.error(f"❌ Error: {st.session_state.get('iol_connection_error', 'Error desconocido')}")
    except Exception as e:
        # Intentar reconectar automáticamente
        if initialize_iol_client():
            st.sidebar.success("✅ Reconectado automáticamente")
            st.rerun()
        else:
            st.sidebar.error(f"Error cargando usuario: {e}")
            if st.sidebar.button("🔄 Reconectar", width='stretch'):
                if initialize_iol_client():
                    st.sidebar.success("✅ Reconectado")
                    st.rerun()
    
    # Navigation - Simplified with single selectbox
    st.sidebar.markdown("### 📍 Navegación")
    
    # Navigation options - All pages in one list for simpler navigation
    all_pages = [
        "🖥️ Command Center",
        "📊 Dashboard en Vivo", 
        "💼 Gestión de Activos",
        "🤖 Bot Autónomo",
        "📊 Operaciones en Tiempo Real",
        "🧬 Optimizador Genético",
        "🧠 Red Neuronal",
        "📉 Estrategias Avanzadas",
        "⚙️ Configuración",
        "⚡ Terminal de Trading",
        "💬 Chat con el Bot"
    ]
    
    # Page mapping (navigation state initialized in dashboard.py before this function is called)
    page_map = {
        "🖥️ Command Center": "Command Center",
        "📊 Dashboard en Vivo": "🏠 Inicio",
        "💼 Gestión de Activos": "💼 Gestión de Activos",
        "🤖 Bot Autónomo": "🤖 Bot Autónomo",
        "📊 Operaciones en Tiempo Real": "📊 Operaciones en Tiempo Real",
        "🧬 Optimizador Genético": "Genetic Optimizer",
        "🧠 Red Neuronal": "Neural Network",
        "📉 Estrategias Avanzadas": "🧬 Estrategias Avanzadas",
        "⚙️ Configuración": "⚙️ Sistema & Configuración",
        "⚡ Terminal de Trading": "⚡ Terminal de Trading",
        "💬 Chat con el Bot": "💬 Chat con el Bot"
    }

    def on_nav_change():
        """Callback para actualizar la página actual cuando cambia la selección"""
        selected = st.session_state.main_navigation
        st.session_state.current_page = page_map.get(selected, "Command Center")
        
    # Selectbox with KEY - Source of Truth
    st.sidebar.selectbox(
        "📍 Navegar a:",
        all_pages,
        key="main_navigation",
        on_change=on_nav_change
    )
    
    # Ensure current_page is set strictly from the navigation state
    if 'current_page' not in st.session_state:
        # Sync initial state
        st.session_state.current_page = page_map.get(st.session_state.main_navigation, "Command Center")
    elif st.session_state.current_page != page_map.get(st.session_state.main_navigation, "Command Center"):
        # Correct drift
        st.session_state.current_page = page_map.get(st.session_state.main_navigation, "Command Center")

    page = st.session_state.current_page

    # DEBUG: Mostrar información de navegación
    if st.sidebar.checkbox("🔍 Debug Navegación", value=False, key="debug_nav"):
        st.sidebar.write(f"**Selección (Key):** {st.session_state.main_navigation}")
        st.sidebar.write(f"**Página actual:** {page}")
    
    st.sidebar.markdown("---")
    
    # System Status
    st.sidebar.markdown("### 🔋 Estado del Sistema")
    bot_running, bot_pid = check_bot_status()
    
    status_emoji = "🟢" if bot_running else "🔴"
    status_text = "ACTIVO" if bot_running else "INACTIVO"
    st.sidebar.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span style="font-size: 1.5rem;">{status_emoji}</span>
            <div>
                <div style="font-weight: 600; color: white;">{status_text}</div>
                <div style="font-size: 0.85rem; color: rgba(255,255,255,0.7);">Bot de Trading</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced Account Info in Sidebar
    st.sidebar.markdown("### 💰 Mi Cuenta")
    
    # Botón para actualizar saldo y reconectar si es necesario
    if st.sidebar.button("🔄 Actualizar Saldo", width='stretch'):
        # Intentar reconectar si no hay cliente o si hay error
        if not st.session_state.get('iol_client') or 'iol_connection_error' in st.session_state:
            if initialize_iol_client():
                st.sidebar.success("✅ Reconectado y saldo actualizado")
                st.rerun()
            else:
                st.sidebar.error(f"❌ Error reconectando: {st.session_state.get('iol_connection_error', 'Error desconocido')}")
                st.rerun()
        else:
            # Forzar actualización del cliente IOL
            try:
                # Intentar obtener saldo actualizado
                st.session_state.iol_client.get_available_balance()
                st.sidebar.success("✅ Saldo actualizado")
                st.rerun()
            except Exception as e:
                # Si falla, intentar reconectar
                st.session_state.iol_client = None
                if initialize_iol_client():
                    st.sidebar.success("✅ Reconectado y saldo actualizado")
                    st.rerun()
                else:
                    st.sidebar.error(f"❌ Error: {e}")
                    st.rerun()
    
    try:
        # Load Portfolio Value
        portfolio = load_portfolio()
        total_portfolio_val = sum(asset.get('total_val', 0) for asset in portfolio) if portfolio else 0.0
        
        # Load Available Balance (Live from IOL) - Usar cliente de sesión si está disponible
        available_balance = 0.0
        balance_error = None
        all_balances = {}
        
        if st.session_state.get('iol_client'):
            try:
                # Intentar obtener saldo inmediato primero
                available_balance = st.session_state.iol_client.get_available_balance(prefer_immediate=True)
                # Si no hay saldo inmediato, intentar T+1
                if available_balance == 0:
                    available_balance = st.session_state.iol_client.get_available_balance(prefer_immediate=False)
                # Obtener todos los saldos para mostrar detalles
                all_balances = st.session_state.iol_client.get_all_balances()
            except Exception as e:
                balance_error = str(e)
                # Intentar crear nuevo cliente como fallback
                try:
                    iol_fallback = IOLClient()
                    available_balance = iol_fallback.get_available_balance(prefer_immediate=True)
                    if available_balance == 0:
                        available_balance = iol_fallback.get_available_balance(prefer_immediate=False)
                    all_balances = iol_fallback.get_all_balances()
                    # Actualizar sesión con el nuevo cliente
                    st.session_state.iol_client = iol_fallback
                except Exception as e2:
                    balance_error = f"Error principal: {e}, Error fallback: {e2}"
        else:
            try:
                # Intentar conectar automáticamente si no hay cliente
                if initialize_iol_client():
                    try:
                        available_balance = st.session_state.iol_client.get_available_balance(prefer_immediate=True)
                        if available_balance == 0:
                            available_balance = st.session_state.iol_client.get_available_balance(prefer_immediate=False)
                        all_balances = st.session_state.iol_client.get_all_balances()
                    except Exception as e:
                        balance_error = str(e)
                else:
                    balance_error = st.session_state.get('iol_connection_error', 'No se pudo conectar a IOL')
            except Exception as e:
                balance_error = str(e)
        
        total_equity = total_portfolio_val + available_balance
        
        # Mostrar saldo con formato mejorado
        if balance_error:
            st.sidebar.warning(f"⚠️ Error obteniendo saldo: {balance_error}")
            st.sidebar.info("💡 Usa el botón 'Actualizar Saldo' para reintentar")
        
        st.sidebar.markdown(f"""
        <div style="background: rgba(255,255,255,0.15); padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: rgba(255,255,255,0.8);">Portafolio:</span>
                <span style="font-weight: 700; color: white;">${total_portfolio_val:,.2f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: rgba(255,255,255,0.8);">Disponible:</span>
                <span style="font-weight: 700; color: white;">${available_balance:,.2f}</span>
            </div>
            <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top: 0.5rem; margin-top: 0.5rem;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: rgba(255,255,255,0.8); font-weight: 600;">Capital Total:</span>
                    <span style="font-weight: 800; color: #4caf50; font-size: 1.1rem;">${total_equity:,.2f}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar también en formato compacto
        st.sidebar.caption(f"💵 ${available_balance:,.2f} ARS disponibles")
        
        # Mostrar desglose de saldos si hay múltiples
        if all_balances and len(all_balances) > 1:
            with st.sidebar.expander("📊 Ver todos los saldos"):
                for liquidacion, saldo in sorted(all_balances.items()):
                    if saldo > 0:
                        liquidacion_display = liquidacion.replace("_", " ").title()
                        st.caption(f"• {liquidacion_display}: ${saldo:,.2f}")
        
    except Exception as e:
        st.sidebar.error(f"❌ Error cargando saldo: {e}")
        st.sidebar.info("💡 Verifica tu conexión con IOL y usa el botón 'Actualizar Saldo'")

    # Quick Stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Estadísticas Rápidas")
    try:
        # Get monitored symbols count
        monitored = get_monitored_symbols()
        st.sidebar.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 0.75rem; border-radius: 8px; margin: 0.25rem 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: rgba(255,255,255,0.8);">Activos Monitoreados:</span>
                <span style="font-weight: 700; color: white; font-size: 1.2rem;">{len(monitored)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except:
        pass
        
    return st.session_state.current_page
