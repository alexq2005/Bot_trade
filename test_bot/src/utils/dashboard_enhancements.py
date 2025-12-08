"""
Utilidades para Mejorar el Dashboard
Visualizaciones avanzadas, filtros, y mejoras de UX
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import streamlit as st


def create_pnl_chart(trades_df: pd.DataFrame, cumulative: bool = True) -> go.Figure:
    """
    Crea un gráfico de P&L interactivo
    
    Args:
        trades_df: DataFrame con trades (debe tener 'timestamp', 'pnl')
        cumulative: Si mostrar P&L acumulado o por trade
    
    Returns:
        Figura de Plotly
    """
    if trades_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    trades_df = trades_df.copy()
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
    trades_df = trades_df.sort_values('timestamp')
    
    if cumulative:
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        y_data = trades_df['cumulative_pnl']
        y_label = "P&L Acumulado"
    else:
        y_data = trades_df['pnl']
        y_label = "P&L por Trade"
    
    fig = go.Figure()
    
    # Línea principal
    fig.add_trace(go.Scatter(
        x=trades_df['timestamp'],
        y=y_data,
        mode='lines+markers',
        name=y_label,
        line=dict(color='#2ecc71' if cumulative else '#3498db', width=2),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>' + y_label + ': $%{y:,.2f}<extra></extra>'
    ))
    
    # Línea de cero
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="Break Even"
    )
    
    fig.update_layout(
        title=f"{y_label} en el Tiempo",
        xaxis_title="Fecha",
        yaxis_title="P&L ($)",
        hovermode='x unified',
        template='plotly_dark',
        height=400
    )
    
    return fig


def create_win_rate_chart(trades_df: pd.DataFrame) -> go.Figure:
    """
    Crea un gráfico de win rate por período
    
    Args:
        trades_df: DataFrame con trades
    
    Returns:
        Figura de Plotly
    """
    if trades_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos disponibles", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    trades_df = trades_df.copy()
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
    trades_df['date'] = trades_df['timestamp'].dt.date
    
    # Calcular win rate diario
    daily_stats = trades_df.groupby('date').agg({
        'pnl': lambda x: (x > 0).sum() / len(x) * 100 if len(x) > 0 else 0
    }).reset_index()
    daily_stats.columns = ['date', 'win_rate']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=daily_stats['date'],
        y=daily_stats['win_rate'],
        name="Win Rate %",
        marker_color='#9b59b6',
        hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<extra></extra>'
    ))
    
    # Línea de promedio
    avg_win_rate = daily_stats['win_rate'].mean()
    fig.add_hline(
        y=avg_win_rate,
        line_dash="dash",
        line_color="yellow",
        annotation_text=f"Promedio: {avg_win_rate:.1f}%"
    )
    
    fig.update_layout(
        title="Win Rate Diario",
        xaxis_title="Fecha",
        yaxis_title="Win Rate (%)",
        template='plotly_dark',
        height=300
    )
    
    return fig


def create_correlation_heatmap(portfolio_df: pd.DataFrame, symbols: List[str]) -> go.Figure:
    """
    Crea un heatmap de correlaciones entre activos
    
    Args:
        portfolio_df: DataFrame con precios históricos (columnas: símbolos)
        symbols: Lista de símbolos a analizar
    
    Returns:
        Figura de Plotly
    """
    if portfolio_df.empty or len(symbols) < 2:
        fig = go.Figure()
        fig.add_annotation(text="Se necesitan al menos 2 símbolos", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Calcular correlaciones
    available_symbols = [s for s in symbols if s in portfolio_df.columns]
    if len(available_symbols) < 2:
        fig = go.Figure()
        fig.add_annotation(text="No hay suficientes datos", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    corr_matrix = portfolio_df[available_symbols].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdYlBu',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        hovertemplate='<b>%{y} vs %{x}</b><br>Correlación: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Matriz de Correlación entre Activos",
        template='plotly_dark',
        height=500,
        width=600
    )
    
    return fig


def create_returns_distribution(trades_df: pd.DataFrame) -> go.Figure:
    """
    Crea un histograma de distribución de retornos
    
    Args:
        trades_df: DataFrame con trades (debe tener 'pnl')
    
    Returns:
        Figura de Plotly
    """
    if trades_df.empty or 'pnl' not in trades_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos disponibles", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    pnl_values = trades_df['pnl'].dropna()
    
    if len(pnl_values) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No hay datos de P&L", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        return fig
    
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=pnl_values,
        nbinsx=30,
        name="Distribución de Retornos",
        marker_color='#3498db',
        hovertemplate='<b>P&L: $%{x:.2f}</b><br>Frecuencia: %{y}<extra></extra>'
    ))
    
    # Línea de media
    mean_pnl = pnl_values.mean()
    fig.add_vline(
        x=mean_pnl,
        line_dash="dash",
        line_color="yellow",
        annotation_text=f"Media: ${mean_pnl:.2f}"
    )
    
    fig.update_layout(
        title="Distribución de Retornos (P&L)",
        xaxis_title="P&L ($)",
        yaxis_title="Frecuencia",
        template='plotly_dark',
        height=400
    )
    
    return fig


def create_performance_metrics_cards(metrics: Dict) -> None:
    """
    Crea tarjetas de métricas de performance en Streamlit
    
    Args:
        metrics: Diccionario con métricas
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_trades = metrics.get('total_trades', 0)
        st.metric("Total Trades", total_trades)
    
    with col2:
        win_rate = metrics.get('win_rate', 0.0)
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    with col3:
        total_pnl = metrics.get('total_pnl', 0.0)
        color = "normal" if total_pnl >= 0 else "inverse"
        st.metric("P&L Total", f"${total_pnl:,.2f}", delta=None)
    
    with col4:
        sharpe = metrics.get('sharpe_ratio', 0.0)
        st.metric("Sharpe Ratio", f"{sharpe:.2f}")


def create_symbol_filter(symbols: List[str], default_selected: Optional[List[str]] = None) -> List[str]:
    """
    Crea un filtro de símbolos mejorado en Streamlit
    
    Args:
        symbols: Lista de símbolos disponibles
        default_selected: Símbolos seleccionados por defecto
    
    Returns:
        Lista de símbolos seleccionados
    """
    if default_selected is None:
        default_selected = symbols[:5] if len(symbols) >= 5 else symbols
    
    selected = st.multiselect(
        "Filtrar por Símbolos",
        options=symbols,
        default=default_selected,
        help="Selecciona los símbolos a mostrar"
    )
    
    return selected if selected else symbols


def create_date_range_filter(default_days: int = 30) -> Tuple[datetime, datetime]:
    """
    Crea un filtro de rango de fechas en Streamlit
    
    Args:
        default_days: Días por defecto hacia atrás
    
    Returns:
        Tupla (fecha_inicio, fecha_fin)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=default_days)
    
    col1, col2 = st.columns(2)
    
    with col1:
        start = st.date_input(
            "Fecha Inicio",
            value=start_date.date(),
            max_value=end_date.date()
        )
    
    with col2:
        end = st.date_input(
            "Fecha Fin",
            value=end_date.date(),
            min_value=start,
            max_value=end_date.date()
        )
    
    return datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.max.time())


def apply_filters(
    df: pd.DataFrame,
    symbols: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_pnl: Optional[float] = None,
    max_pnl: Optional[float] = None
) -> pd.DataFrame:
    """
    Aplica filtros a un DataFrame
    
    Args:
        df: DataFrame a filtrar
        symbols: Lista de símbolos a incluir
        start_date: Fecha de inicio
        end_date: Fecha de fin
        min_pnl: P&L mínimo
        max_pnl: P&L máximo
    
    Returns:
        DataFrame filtrado
    """
    filtered_df = df.copy()
    
    if 'symbol' in filtered_df.columns and symbols:
        filtered_df = filtered_df[filtered_df['symbol'].isin(symbols)]
    
    if 'timestamp' in filtered_df.columns:
        if start_date:
            filtered_df = filtered_df[pd.to_datetime(filtered_df['timestamp']) >= start_date]
        if end_date:
            filtered_df = filtered_df[pd.to_datetime(filtered_df['timestamp']) <= end_date]
    
    if 'pnl' in filtered_df.columns:
        if min_pnl is not None:
            filtered_df = filtered_df[filtered_df['pnl'] >= min_pnl]
        if max_pnl is not None:
            filtered_df = filtered_df[filtered_df['pnl'] <= max_pnl]
    
    return filtered_df

