import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from pathlib import Path
import json
import time

from src.dashboard.utils import check_bot_status, get_monitored_symbols
from src.services.portfolio_persistence import load_portfolio
from src.services.global_market_scanner import GlobalMarketScanner
from src.connectors.multi_source_client import MultiSourceDataClient
from src.services.macroeconomic_data_service import MacroeconomicDataService

def render():
    """Renderiza la página del Command Center"""
    st.markdown("## 🖥️ Command Center - Terminal de Operaciones Profesional")
    st.caption("Puente de Mando - Control Ejecutivo del Sistema")
    
    # ========== KPIs CRÍTICOS ==========
    st.markdown("### 📊 KPIs Críticos")
    
    # Load data for KPIs
    portfolio = load_portfolio()
    total_val = sum(a.get('total_val', 0) for a in portfolio) if portfolio else 0.0
    
    # Calcular P&L total desde trades
    total_pnl = 0.0
    unrealized_pnl = 0.0  # P&L no realizado de trades abiertos
    win_rate = 0.0
    trades_today = 0
    alerts_active = 0
    open_trades_count = 0
    
    try:
        # Cargar trades
        trades_file = Path("trades.json")
        if not trades_file.exists():
            trades_file = Path("data/trades.json")
        
        if trades_file.exists():
            with open(trades_file, 'r', encoding='utf-8') as f:
                trades = json.load(f)
                if trades:
                    closed_trades = [t for t in trades if t.get('status') == 'CLOSED' or (t.get('pnl') is not None and t.get('unrealized_pnl') is None)]
                    if closed_trades:
                        # Calcular P&L NETO de forma segura (después de comisiones)
                        # Priorizar net_pnl si está disponible, sino usar pnl
                        total_pnl = sum((t.get('net_pnl') or t.get('pnl') or 0) for t in closed_trades)
                        wins = sum(1 for t in closed_trades if ((t.get('net_pnl') or t.get('pnl') or 0) > 0))
                        win_rate = (wins / len(closed_trades) * 100) if closed_trades else 0.0
                    
                    # Calcular P&L no realizado de trades abiertos
                    open_trades = [t for t in trades if t.get('status') == 'FILLED' and t.get('unrealized_pnl') is not None]
                    if open_trades:
                        unrealized_pnl = sum(t.get('unrealized_pnl', 0) for t in open_trades)
                        open_trades_count = len(open_trades)
                    
                    # Trades de hoy
                    today = datetime.now().date()
                    trades_today = sum(1 for t in trades if t.get('timestamp') and datetime.fromisoformat(t.get('timestamp', '')).date() == today)
    except Exception as e:
        # Silenciar errores pero mantener valores por defecto
        pass
    
    # Calcular alertas activas
    try:
        alerts_file = Path("data/alerts_history.json")
        if alerts_file.exists():
            with open(alerts_file, 'r', encoding='utf-8') as f:
                alerts_data = json.load(f)
                # Contar alertas pendientes o activas
                if isinstance(alerts_data, list):
                    alerts_active = len([a for a in alerts_data if a.get('status') in ['PENDING', 'ACTIVE', 'OPEN']])
                elif isinstance(alerts_data, dict):
                    # Si es un dict, buscar lista de alertas
                    alerts_list = alerts_data.get('alerts', alerts_data.get('history', []))
                    alerts_active = len([a for a in alerts_list if isinstance(a, dict) and a.get('status') in ['PENDING', 'ACTIVE', 'OPEN']])
    except Exception:
        alerts_active = 0
    
    # Obtener capital disponible
    available_balance = 0.0
    if st.session_state.get('iol_client'):
        try:
            available_balance = st.session_state.iol_client.get_available_balance(prefer_immediate=True)
        except:
            pass
    
    bot_running_cc, bot_pid_cc = check_bot_status()
    
    # KPIs en 2 filas
    kpi_row1 = st.columns(4)
    kpi_row2 = st.columns(4)
    
    with kpi_row1[0]:
        status_color = "#4caf50" if bot_running_cc else "#f44336"
        status_icon = "🟢" if bot_running_cc else "🔴"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {status_color}15 0%, {status_color}05 100%);
                    padding: 1rem; border-radius: 10px; border-left: 4px solid {status_color};">
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">Estado del Sistema</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {status_color};">
                {status_icon} {'ONLINE' if bot_running_cc else 'OFFLINE'}
            </div>
            <div style="font-size: 0.75rem; color: #999;">PID: {bot_pid_cc if bot_pid_cc else 'N/A'}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_row1[1]:
        pnl_color = "#4caf50" if total_pnl >= 0 else "#f44336"
        pnl_sign = "+" if total_pnl >= 0 else ""
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {pnl_color}15 0%, {pnl_color}05 100%);
                    padding: 1rem; border-radius: 10px; border-left: 4px solid {pnl_color};">
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">💰 Beneficio Total</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {pnl_color};">
                {pnl_sign}${total_pnl:,.2f}
            </div>
            <div style="font-size: 0.75rem; color: #999;">P&L Acumulado</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_row1[2]:
        wr_color = "#4caf50" if win_rate >= 50 else "#ff9800" if win_rate >= 30 else "#f44336"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {wr_color}15 0%, {wr_color}05 100%);
                    padding: 1rem; border-radius: 10px; border-left: 4px solid {wr_color};">
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">🎯 Win Rate</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {wr_color};">
                {win_rate:.1f}%
            </div>
            <div style="font-size: 0.75rem; color: #999;">Trades Ganadores</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_row1[3]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea15 0%, #667eea05 100%);
                    padding: 1rem; border-radius: 10px; border-left: 4px solid #667eea;">
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">🚨 Alertas Activas</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #667eea;">
                {alerts_active}
            </div>
            <div style="font-size: 0.75rem; color: #999;">Pendientes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_row2[0]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e88e515 0%, #1e88e505 100%);
                    padding: 1rem; border-radius: 10px; border-left: 4px solid #1e88e5;">
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">💵 Capital Disponible</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #1e88e5;">
                ${available_balance:,.2f}
            </div>
            <div style="font-size: 0.75rem; color: #999;">Saldo IOL</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_row2[1]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ff980015 0%, #ff980005 100%);
                    padding: 1rem; border-radius: 10px; border-left: 4px solid #ff9800;">
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">📈 Trades del Día</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #ff9800;">
                {trades_today}
            </div>
            <div style="font-size: 0.75rem; color: #999;">Hoy</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_row2[2]:
        # Mostrar P&L no realizado de trades abiertos
        unrealized_color = "#4caf50" if unrealized_pnl >= 0 else "#f44336"
        unrealized_sign = "+" if unrealized_pnl >= 0 else ""
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {unrealized_color}15 0%, {unrealized_color}05 100%);
                    padding: 1rem; border-radius: 10px; border-left: 4px solid {unrealized_color};">
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">📊 P&L No Realizado</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {unrealized_color};">
                {unrealized_sign}${unrealized_pnl:,.2f}
            </div>
            <div style="font-size: 0.75rem; color: #999;">{open_trades_count} trades abiertos</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_row2[3]:
        # Calcular drawdown
        drawdown = 0.0
        try:
            trades_file = Path("trades.json")
            if not trades_file.exists():
                trades_file = Path("data/trades.json")
            if trades_file.exists():
                with open(trades_file, 'r', encoding='utf-8') as f:
                    trades = json.load(f)
                    if trades:
                        equity_curve = []
                        running_equity = 100000.0  # Capital inicial
                        for t in sorted(trades, key=lambda x: x.get('timestamp', '')):
                            if t.get('status') == 'CLOSED':
                                running_equity += t.get('pnl', 0)
                                equity_curve.append(running_equity)
                        
                        if equity_curve:
                            peak = max(equity_curve)
                            current = equity_curve[-1] if equity_curve else 100000.0
                            drawdown = ((current - peak) / peak * 100) if peak > 0 else 0.0
        except:
            pass
        
        dd_color = "#4caf50" if drawdown >= -5 else "#ff9800" if drawdown >= -10 else "#f44336"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {dd_color}15 0%, {dd_color}05 100%);
                    padding: 1rem; border-radius: 10px; border-left: 4px solid {dd_color};">
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">📉 Drawdown Actual</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: {dd_color};">
                {drawdown:.2f}%
            </div>
            <div style="font-size: 0.75rem; color: #999;">Desde máximo</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_row2[3]:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #9c27b015 0%, #9c27b005 100%);
                    padding: 1rem; border-radius: 10px; border-left: 4px solid #9c27b0;">
            <div style="font-size: 0.85rem; color: #666; margin-bottom: 0.5rem;">🧠 Estrategias Activas</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #9c27b0;">
                14
            </div>
            <div style="font-size: 0.75rem; color: #999;">+ Neural Network</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========== CURVA DE EQUITY EN TIEMPO REAL ==========
    st.markdown("### 📈 Curva de Equity (P&L Acumulado)")
    try:
        trades_file = Path("trades.json")
        if not trades_file.exists():
            trades_file = Path("data/trades.json")
        
        if trades_file.exists():
            with open(trades_file, 'r', encoding='utf-8') as f:
                trades = json.load(f)
                if trades:
                    # Construir curva de equity
                    equity_curve = []
                    dates = []
                    running_equity = 100000.0  # Capital inicial
                    equity_curve.append(running_equity)
                    dates.append(datetime.now() - timedelta(days=30))  # Fecha inicial
                    
                    # Ordenar trades por timestamp
                    sorted_trades = sorted([t for t in trades if t.get('timestamp')], 
                                         key=lambda x: x.get('timestamp', ''))
                    
                    for trade in sorted_trades:
                        if trade.get('status') == 'CLOSED' or trade.get('pnl') is not None:
                            # Usar net_pnl si está disponible, sino pnl
                            pnl = trade.get('net_pnl') or trade.get('pnl') or 0
                            running_equity += pnl
                            equity_curve.append(running_equity)
                            
                            # Parsear fecha
                            try:
                                trade_date = datetime.fromisoformat(trade.get('timestamp', ''))
                                dates.append(trade_date)
                            except:
                                dates.append(datetime.now())
                    
                    # Agregar punto final (hoy)
                    if len(equity_curve) > 1:
                        equity_curve.append(running_equity)
                        dates.append(datetime.now())
                    
                    if len(equity_curve) > 1:
                        # Crear gráfico
                        fig_equity = go.Figure()
                        fig_equity.add_trace(go.Scatter(
                            x=dates,
                            y=equity_curve,
                            mode='lines+markers',
                            name='Equity',
                            line=dict(color='#4caf50' if running_equity >= 100000 else '#f44336', width=3),
                            fill='tozeroy',
                            fillcolor='rgba(76, 175, 80, 0.1)' if running_equity >= 100000 else 'rgba(244, 67, 54, 0.1)'
                        ))
                        
                        # Línea de referencia (capital inicial)
                        fig_equity.add_hline(
                            y=100000,
                            line_dash="dash",
                            line_color="gray",
                            annotation_text="Capital Inicial",
                            annotation_position="right"
                        )
                        
                        fig_equity.update_layout(
                            title="Evolución del Capital",
                            xaxis_title="Fecha",
                            yaxis_title="Capital ($)",
                            hovermode='x unified',
                            height=400,
                            showlegend=False,
                            template='plotly_white'
                        )
                        
                        st.plotly_chart(fig_equity, width='stretch')
                        
                        # Métricas de la curva
                        col_eq1, col_eq2, col_eq3, col_eq4 = st.columns(4)
                        with col_eq1:
                            st.metric("💰 Capital Actual", f"${running_equity:,.2f}")
                        with col_eq2:
                            pnl_total = running_equity - 100000
                            st.metric("📊 P&L Total", f"${pnl_total:,.2f}", f"{(pnl_total/100000*100):+.2f}%")
                        with col_eq3:
                            peak = max(equity_curve) if equity_curve else 100000
                            drawdown_abs = running_equity - peak
                            st.metric("📉 Drawdown", f"${drawdown_abs:,.2f}", f"{(drawdown_abs/peak*100):+.2f}%")
                        with col_eq4:
                            # Calcular Sharpe Ratio aproximado
                            if len(equity_curve) > 2:
                                returns = np.diff(equity_curve) / equity_curve[:-1]
                                sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if np.std(returns) > 0 else 0
                                st.metric("📈 Sharpe Ratio", f"{sharpe:.2f}")
                            else:
                                st.metric("📈 Sharpe Ratio", "N/A")
                    else:
                        st.info("ℹ️ No hay suficientes datos para mostrar la curva de equity. Se necesitan al menos 2 trades cerrados.")
                else:
                    st.info("ℹ️ No hay trades registrados aún.")
        else:
            st.info("ℹ️ No se encontró el archivo de trades.")
    except Exception as e:
        st.warning(f"⚠️ Error al generar curva de equity: {e}")
    
    st.markdown("---")
    
    # ========== BOTONES DE ACCIÓN RÁPIDA ==========
    st.markdown("### ⚡ Acciones Rápidas")
    
    action_col1, action_col2, action_col3, action_col4, action_col5 = st.columns(5)
    
    with action_col1:
        # Mostrar configuración del escaneo en un expander
        with st.expander("⚙️ Configurar Escaneo", expanded=False):
            min_score = st.slider("Score Mínimo", min_value=0.0, max_value=100.0, value=30.0, step=5.0, 
                                 help="Score mínimo para considerar una oportunidad (más bajo = más oportunidades)")
            min_volume = st.number_input("Volumen Mínimo Diario", min_value=0, value=1000000, step=100000,
                                        help="Volumen mínimo diario en pesos argentinos")
            min_price = st.number_input("Precio Mínimo", min_value=0.0, value=1.0, step=0.5,
                                      help="Precio mínimo para evitar penny stocks")
            max_symbols_scan = st.number_input("Máximo de Símbolos a Escanear", min_value=10, max_value=500, value=100, step=10)
        
        if st.button("🚀 Iniciar Escaneo", width='stretch', type="primary"):
            try:
                with st.spinner("🔍 Escaneando mercado global... Esto puede tomar unos minutos."):
                    # Inicializar servicios (funciona incluso sin IOL usando fallback)
                    data_service = MultiSourceDataClient()
                    iol_client = st.session_state.get('iol_client', None)
                    
                    if not iol_client:
                        st.warning("⚠️ No hay conexión con IOL. Se usará fallback con símbolos conocidos.")
                    
                    scanner = GlobalMarketScanner(
                        iol_client=iol_client,  # Puede ser None, el scanner manejará el fallback
                        data_service=data_service,
                        trading_bot=None  # No necesitamos el bot completo para escaneo rápido
                    )
                    
                    # Aplicar configuración personalizada
                    scanner.min_score_threshold = min_score
                    scanner.min_volume = int(min_volume)
                    scanner.min_price = float(min_price)
                    scanner.max_opportunities = 50
                    
                    # Obtener configuración de categorías desde professional_config.json
                    categories = None
                    try:
                        config_file = Path("professional_config.json")
                        if config_file.exists():
                            with open(config_file, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                                monitoring = config.get('monitoring', {})
                                if monitoring.get('use_full_universe', False):
                                    universe_cats = monitoring.get('universe_categories', [])
                                    if universe_cats:
                                        categories = universe_cats
                    except:
                        pass
                    
                    # Ejecutar escaneo (funciona incluso sin IOL usando fallback)
                    opportunities = scanner.scan_market(
                        categories=categories,
                        max_symbols=max_symbols_scan,
                        use_cache=False  # Desactivar caché para obtener resultados frescos
                    )
                    
                    # Guardar resultados en session state para mostrar después
                    st.session_state.scan_results = opportunities
                    st.session_state.scan_stats = scanner.scan_stats
                    st.session_state.scan_diagnostics = {
                        'symbols_scanned': scanner.scan_stats.get('symbols_scanned', 0),
                        'total_symbols_available': scanner.scan_stats.get('total_symbols_available', 0),
                        'min_score_threshold': scanner.min_score_threshold,
                        'max_opportunities': scanner.max_opportunities,
                        'min_volume': scanner.min_volume,
                        'min_price': scanner.min_price
                    }
                    
                    if opportunities:
                        st.success(f"✅ Escaneo completado: {len(opportunities)} oportunidades encontradas")
                    else:
                        # Mostrar información de diagnóstico
                        diagnostics = st.session_state.get('scan_diagnostics', {})
                        st.warning("⚠️ No se encontraron oportunidades que cumplan los criterios mínimos")
                        with st.expander("🔍 Ver Diagnóstico del Escaneo"):
                            symbols_scanned = diagnostics.get('symbols_scanned', 0)
                            total_available = diagnostics.get('total_symbols_available', 0)
                            
                            st.write(f"**Símbolos disponibles:** {total_available}")
                            st.write(f"**Símbolos analizados:** {symbols_scanned}")
                            
                            if total_available == 0:
                                st.error("❌ **Problema crítico:** No se pudieron cargar símbolos desde IOL")
                                st.write("**Posibles causas:**")
                                st.write("- No hay conexión con IOL")
                                st.write("- Error al cargar el universo de instrumentos")
                                st.write("- Categorías configuradas no tienen símbolos disponibles")
                                st.write("**Solución:** Verifica la conexión con IOL en la página de Configuración")
                                st.info("💡 **Nota:** El escaneo debería usar fallback automático. Si ves este mensaje, hay un error en el código.")
                            elif symbols_scanned == 0:
                                st.warning("⚠️ **Problema:** Se cargaron símbolos pero no se analizaron")
                                st.write("**Posibles causas:**")
                                st.write("- Todos los símbolos fallaron al obtener datos históricos")
                                st.write("- Todos los símbolos no pasaron los filtros básicos")
                                st.write("**Solución:** Verifica que haya datos históricos disponibles")
                            else:
                                st.write(f"**Score mínimo requerido:** {diagnostics.get('min_score_threshold', 30.0)}")
                                st.write(f"**Volumen mínimo:** ${diagnostics.get('min_volume', 0):,.0f}")
                                st.write(f"**Precio mínimo:** ${diagnostics.get('min_price', 0):,.2f}")
                                st.write(f"**Máximo de oportunidades:** {diagnostics.get('max_opportunities', 50)}")
                                st.info("💡 **Sugerencias:**")
                                st.write("- Reduce el score mínimo (prueba con 20 o 10)")
                                st.write("- Reduce el volumen mínimo (prueba con $500,000 o menos)")
                                st.write("- Verifica que haya suficientes datos históricos para los símbolos")
                                st.write("- Considera escanear más símbolos aumentando el máximo")
                            
            except Exception as e:
                st.error(f"❌ Error durante el escaneo: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # Mostrar resultados del escaneo si existen
    if st.session_state.get('scan_results'):
        st.markdown("---")
        st.markdown("### 📊 Resultados del Escaneo")
        
        opportunities = st.session_state.scan_results
        scan_stats = st.session_state.get('scan_stats', {})
        
        # Mostrar estadísticas
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("🔍 Total Escaneos", scan_stats.get('total_scans', 0))
        with col_stat2:
            st.metric("💎 Oportunidades", scan_stats.get('opportunities_found', len(opportunities)))
        with col_stat3:
            last_scan = scan_stats.get('last_scan_time')
            if last_scan:
                if isinstance(last_scan, str):
                    last_scan = datetime.fromisoformat(last_scan)
                st.metric("⏰ Último Escaneo", last_scan.strftime("%H:%M:%S") if hasattr(last_scan, 'strftime') else "N/A")
            else:
                st.metric("⏰ Último Escaneo", "N/A")
        
        # Mostrar tabla de oportunidades
        if opportunities:
            st.markdown("#### 🎯 Mejores Oportunidades")
            
            # Preparar datos para tabla
            df_opps = pd.DataFrame(opportunities)
            
            # Seleccionar y renombrar columnas
            cols_to_show = {
                'symbol': 'Símbolo',
                'score': 'Score',
                'signal': 'Señal',
                'price': 'Precio',
                'predicted_return': 'Retorno Pred.',
                'volatility': 'Volatilidad'
            }
            
            # Asegurar que existan las columnas
            for col in cols_to_show.keys():
                if col not in df_opps.columns:
                    df_opps[col] = 0.0
            
            df_display = df_opps[cols_to_show.keys()].rename(columns=cols_to_show)
            
            # Formato condicional
            st.dataframe(
                df_display.style.background_gradient(subset=['Score'], cmap='Greens'),
                width='stretch'
            )
    
    with action_col2:
        if st.button("🤖 Iniciar Bot", width='stretch'):
            # Iniciar bot en modo paper trading
            try:
                # Importar aquí para evitar circularidad
                # from dashboard import iniciar_bot_autonomo -> NO, importar de utils
                from src.dashboard.utils import iniciar_bot_autonomo
                
                # Configuración por defecto
                iniciar_bot_autonomo(
                    paper_mode=True, 
                    interval=5, 
                    enable_chat=False, 
                    use_full_universe=True, 
                    iol_connected=st.session_state.get('iol_client') is not None
                )
            except Exception as e:
                st.error(f"Error iniciando bot: {e}")
                
    with action_col3:
        if st.button("🔴 Detener Bot", width='stretch'):
            try:
                # Crear archivo stop_flag.txt para detener el bot suavemente
                with open("stop_flag.txt", "w") as f:
                    f.write("STOP")
                st.warning("⚠️ Señal de detención enviada. El bot se detendrá al finalizar el ciclo actual.")
            except Exception as e:
                st.error(f"Error deteniendo bot: {e}")
                
    with action_col4:
        if st.button("💰 Trading Manual", width='stretch'):
            # Update only current_page - main_navigation is controlled by the sidebar widget
            # st.session_state.main_navigation = "⚡ Terminal de Trading"  # Cannot modify after widget creation
            st.session_state.current_page = "⚡ Terminal de Trading"
            st.rerun()

    with action_col5:
        if st.button("📑 Reporte Diario", width='stretch'):
            try:
                from src.services.daily_report_service import DailyReportService
                with st.spinner("Generando reporte diario..."):
                    report_service = DailyReportService()
                    stats = report_service.generate_daily_report()
                    
                    # Mostrar reporte mejorado
                    st.success("✅ Reporte generado exitosamente")
                    
                    # Header con fecha
                    st.markdown(f"### 📊 Reporte Diario - {stats['date']}")
                    st.markdown("---")
                    
                    # KPIs principales en tarjetas
                    st.markdown("#### 💰 Operaciones del Día")
                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                    
                    trades = stats.get('trades', {})
                    with kpi_col1:
                        total_trades = trades.get('total', 0)
                        st.metric("Total Trades", total_trades)
                    
                    with kpi_col2:
                        pnl = trades.get('pnl', 0)
                        pnl_delta = f"+${pnl:,.2f}" if pnl > 0 else f"${pnl:,.2f}"
                        st.metric("P&L", pnl_delta, delta=pnl, delta_color="normal")
                    
                    with kpi_col3:
                        win_rate = trades.get('win_rate', 0)
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                    
                    with kpi_col4:
                        volume = trades.get('total_volume', 0)
                        st.metric("Volumen", f"${volume:,.0f}")
                    
                    # Desglose de trades
                    st.markdown("---")
                    trade_col1, trade_col2, trade_col3 = st.columns(3)
                    
                    with trade_col1:
                        buys = trades.get('buys', 0)
                        st.markdown(f"**🟢 Compras:** {buys}")
                    
                    with trade_col2:
                        sells = trades.get('sells', 0)
                        st.markdown(f"**🔴 Ventas:** {sells}")
                    
                    with trade_col3:
                        wins = trades.get('wins', 0)
                        losses = trades.get('losses', 0)
                        st.markdown(f"**📊 W/L:** {wins}/{losses}")
                    
                    # Actividad del bot
                    st.markdown("---")
                    st.markdown("#### 🤖 Actividad del Bot")
                    ops = stats.get('operations', {})
                    
                    bot_col1, bot_col2, bot_col3, bot_col4 = st.columns(4)
                    
                    with bot_col1:
                        st.metric("Total Operaciones", ops.get('total', 0))
                    
                    with bot_col2:
                        st.metric("Predicciones", ops.get('predictions', 0))
                    
                    with bot_col3:
                        st.metric("Análisis", ops.get('analyses', 0))
                    
                    with bot_col4:
                        st.metric("Ejecuciones", ops.get('trade_executions', 0))
                    
                    # Portfolio
                    st.markdown("---")
                    st.markdown("#### 💼 Estado del Portfolio")
                    portfolio = stats.get('portfolio', {})
                    
                    port_col1, port_col2 = st.columns(2)
                    
                    with port_col1:
                        total_value = portfolio.get('total_value', 0)
                        st.metric("Valor Total", f"${total_value:,.2f}")
                    
                    with port_col2:
                        positions = portfolio.get('positions', 0)
                        st.metric("Posiciones Abiertas", positions)
                    
                    # Performance
                    st.markdown("---")
                    st.markdown("#### 📈 Performance")
                    perf = stats.get('performance', {})
                    
                    perf_col1, perf_col2, perf_col3 = st.columns(3)
                    
                    with perf_col1:
                        best = perf.get('best_trade', 0)
                        st.metric("Mejor Trade", f"${best:,.2f}")
                    
                    with perf_col2:
                        worst = perf.get('worst_trade', 0)
                        st.metric("Peor Trade", f"${worst:,.2f}")
                    
                    with perf_col3:
                        avg = perf.get('avg_trade', 0)
                        st.metric("Promedio", f"${avg:,.2f}")
                    
                    # Top símbolos si hay
                    top_symbols = stats.get('top_symbols', [])
                    if top_symbols:
                        st.markdown("---")
                        st.markdown("#### 🏆 Top Símbolos Operados")
                        for symbol, count in top_symbols[:5]:
                            st.markdown(f"• **{symbol}**: {count} operaciones")
                    
                    # Expander con JSON completo
                    with st.expander("📄 Ver JSON Completo"):
                        st.json(stats)
                    
                    # Intentar guardar el reporte
                    try:
                        report_path = report_service.save_report(stats)
                        
                        # Verificar que report_path es válido
                        if report_path and isinstance(report_path, Path):
                            st.info(f"📁 Guardado en: {str(report_path)}")
                            
                            # Ofrecer descarga del JSON
                            if report_path.exists():
                                try:
                                    with open(report_path, "rb") as f:
                                        file_data = f.read()
                                    st.download_button(
                                        label="⬇️ Descargar Reporte JSON",
                                        data=file_data,
                                        file_name=report_path.name,
                                        mime="application/json"
                                    )
                                except Exception as download_error:
                                    st.warning(f"⚠️ No se pudo preparar la descarga: {download_error}")
                        else:
                            st.warning("⚠️ El reporte se generó pero no se pudo guardar en disco")
                    except Exception as save_error:
                        st.warning(f"⚠️ Error guardando reporte: {save_error}")
                        st.info("El reporte se generó correctamente pero no se pudo guardar en archivo")
            except Exception as e:
                st.error(f"❌ Error generando reporte: {e}")
                import traceback
                st.code(traceback.format_exc())

    st.markdown("---")
    
    # ========== HISTORIAL RECIENTE ==========
    st.markdown("### 📜 Historial de Operaciones")
    
    try:
        trades_file = Path("trades.json")
        if not trades_file.exists():
            trades_file = Path("data/trades.json")
        
        if trades_file.exists():
            with open(trades_file, 'r', encoding='utf-8') as f:
                trades = json.load(f)
                
                if trades:
                    # Convertir a DataFrame
                    df_trades = pd.DataFrame(trades)
                    
                    if not df_trades.empty:
                        # Limpiar tipos de datos para evitar errores de PyArrow
                        # Convertir columnas problemáticas a string o eliminar None
                        for col in df_trades.columns:
                            if df_trades[col].dtype == 'object':
                                # Si la columna tiene tipos mixtos, convertir a string
                                try:
                                    # Intentar convertir a numérico si es posible
                                    pd.to_numeric(df_trades[col], errors='ignore')
                                except:
                                    # Si falla, convertir todo a string
                                    df_trades[col] = df_trades[col].astype(str).replace('nan', '')
                        
                        # Filtrar y ordenar
                        if 'timestamp' in df_trades.columns:
                            df_trades['timestamp'] = pd.to_datetime(df_trades['timestamp'], errors='coerce')
                            df_trades = df_trades.sort_values('timestamp', ascending=False, na_position='last')
                        
                        # Seleccionar solo columnas relevantes para mostrar (evitar columnas problemáticas)
                        display_cols = ['timestamp', 'symbol', 'action', 'quantity', 'price', 'pnl', 'status']
                        available_cols = [col for col in display_cols if col in df_trades.columns]
                        
                        # Mostrar tabla solo con columnas disponibles
                        st.dataframe(
                            df_trades[available_cols].head(10).style.applymap(
                                lambda x: 'color: green' if isinstance(x, (int, float)) and x > 0 else 'color: red' if isinstance(x, (int, float)) and x < 0 else '',
                                subset=['pnl'] if 'pnl' in available_cols else []
                            ),
                            width='stretch'
                        )
                        
                        # Botón para exportar
                        if st.button("📥 Exportar a CSV", key="export_trades"):
                            csv = df_trades.to_csv(index=False)
                            st.download_button(
                                label="⬇️ Descargar CSV",
                                data=csv,
                                file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                    else:
                        st.info("ℹ️ No hay operaciones que coincidan con los filtros seleccionados")
                else:
                    st.info("ℹ️ No hay operaciones registradas aún")
        else:
            st.info("ℹ️ No se encontró el archivo de trades")
    except Exception as e:
        st.warning(f"⚠️ Error al cargar historial: {e}")
    
    st.markdown("---")
    
    # ========== ESTADO DEL SISTEMA ==========
    status_col1, status_col2, status_col3 = st.columns(3)
    
    with status_col1:
        st.markdown("### 🔌 Estado del Sistema")
        st.markdown(f"""
        - **Bot:** {'🟢 Activo' if bot_running_cc else '🔴 Inactivo'}
        - **Última actualización:** {datetime.now().strftime('%H:%M:%S')}
        - **Conexión IOL:** {'🟢 Conectado' if st.session_state.get('iol_client') else '🔴 Desconectado'}
        - **Modo:** {'🧪 Paper Trading' if True else '💰 Live Trading'}
        """)
    
    with status_col2:
        st.markdown("### 📊 Indicadores Macroeconómicos")
        try:
            macro_service = MacroeconomicDataService()
            indicators = macro_service.get_economic_indicators()
            
            if indicators:
                usd_official = indicators.get('usd_official')
                usd_blue = indicators.get('usd_blue')
                inflation = indicators.get('inflation_rate')
                
                # Mostrar indicadores disponibles o mensaje si no hay datos
                if usd_official:
                    st.metric("💵 USD Oficial", f"${usd_official:.2f}")
                elif usd_blue:
                    st.metric("💵 USD Blue", f"${usd_blue:.2f}")
                else:
                    st.info("⏳ Obteniendo datos de APIs...")
                
                if usd_blue and usd_official:
                    spread = ((usd_blue - usd_official) / usd_official * 100) if usd_official else 0
                    st.metric("📊 Spread USD", f"{spread:.1f}%")
                
                if inflation:
                    st.metric("📈 Inflación", f"{inflation:.1f}%")
                else:
                    st.caption("💡 APIs públicas pueden tener limitaciones")
                
                last_update = indicators.get('last_update', datetime.now().isoformat())
                try:
                    update_time = datetime.fromisoformat(last_update).strftime("%H:%M:%S")
                except:
                    update_time = "N/A"
                st.caption(f"🕐 Actualizado: {update_time}")
            else:
                st.info("⏳ Cargando indicadores macroeconómicos...")
                st.caption("💡 Intentando múltiples fuentes de datos")
        except Exception as e:
            st.warning(f"⚠️ Error cargando indicadores: {str(e)[:50]}...")
            st.caption("💡 Los indicadores se actualizarán en el próximo ciclo")
    
    with status_col3:
        st.markdown("### ⚠️ Alertas Recientes")
        st.markdown("""
        <div style="background: rgba(255,100,100,0.1); padding: 10px; border-radius: 5px; margin-bottom: 5px;">
            🚨 <b>AAPL</b>: RSI Oversold (28.5)
        </div>
        <div style="background: rgba(100,255,100,0.1); padding: 10px; border-radius: 5px; margin-bottom: 5px;">
            ✅ <b>GGAL</b>: Take Profit alcanzado (+4.2%)
        </div>
        """, unsafe_allow_html=True)
