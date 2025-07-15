import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Trading Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejor apariencia
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
    }
    
    .success-metric {
        border-left-color: #10b981;
    }
    
    .warning-metric {
        border-left-color: #f59e0b;
    }
    
    .danger-metric {
        border-left-color: #ef4444;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📊 Trading Analytics Dashboard</h1>', unsafe_allow_html=True)

# Initialize session state
if 'trades_df' not in st.session_state:
    st.session_state.trades_df = pd.DataFrame()

# Sidebar para configuraciones
st.sidebar.header("⚙️ Configuraciones")

# Tab layout para diferentes métodos de entrada
tab1, tab2 = st.tabs(["📤 Subir CSV", "✏️ Ingresar Manualmente"])

with tab1:
    st.subheader("📁 Subir archivo CSV de trades")
    archivo = st.file_uploader("Arrastra tu archivo CSV aquí", type="csv", key="csv_uploader")
    
    if archivo:
        try:
            df = pd.read_csv(archivo)
            df = df[df['Profit (USD)'] != 0]
            df['Duration (hours)'] = (pd.to_datetime(df['Close Time']) - pd.to_datetime(df['Open Time'])).dt.total_seconds() / 3600
            df['Result'] = df['Profit (USD)'].apply(lambda x: 'Win' if x > 0 else 'Loss')
            
            if 'Order ID' in df.columns:
                df = df.drop(columns=['Order ID'])
            
            st.session_state.trades_df = df
            st.success("✅ Datos cargados correctamente desde CSV!")
            
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo CSV: {str(e)}")

with tab2:
    st.subheader("✏️ Ingresar Trade Manualmente")
    
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            market = st.selectbox("Market", ["STOCK", "FOREX", "CRYPTO", "FUTURES"])
            portfolio = st.text_input("Portfolio", "My Portfolio")
            symbol = st.text_input("Symbol", "AAPL")
            action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
            
        with col2:
            trade_date = st.date_input("Date", datetime.now())
            trade_time = st.time_input("Time", datetime.now().time())
            size = st.number_input("Share/Contracts", min_value=0.0, step=0.01, format="%.2f")
            price = st.number_input("Price", min_value=0.0, step=0.0001, format="%.4f")
        
        commission = st.number_input("Commission", min_value=0.0, step=0.01, format="%.2f")
        fees = st.number_input("Fees", min_value=0.0, step=0.01, format="%.2f")
        profit = st.number_input("Profit (USD)", step=0.01, format="%.2f")
        
        submitted = st.form_submit_button("➕ Agregar Trade")
        
        if submitted:
            if symbol and price > 0 and size > 0:
                new_trade = {
                    'Market': market,
                    'Portfolio': portfolio,
                    'Symbol': symbol.upper(),
                    'Side': action,
                    'Open Time': f"{trade_date} {trade_time}",
                    'Size': size,
                    'Open Price': price,
                    'Commission': commission,
                    'Fees': fees,
                    'Profit (USD)': profit,
                    'Close Time': f"{trade_date} {trade_time}",
                    'Take Profit': None,
                    'Stop Loss': None
                }
                
                new_trade_df = pd.DataFrame([new_trade])
                
                if st.session_state.trades_df.empty:
                    st.session_state.trades_df = new_trade_df
                else:
                    st.session_state.trades_df = pd.concat([st.session_state.trades_df, new_trade_df], ignore_index=True)
                
                st.success("✅ Trade agregado exitosamente!")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("⚠️ Por favor complete los campos requeridos (Symbol, Size, Price)")

# Análisis principal
if not st.session_state.trades_df.empty:
    df = st.session_state.trades_df.copy()
    
    # Preparar datos
    if 'Duration (hours)' not in df.columns:
        df['Duration (hours)'] = (pd.to_datetime(df['Close Time']) - pd.to_datetime(df['Open Time'])).dt.total_seconds() / 3600
    
    if 'Result' not in df.columns:
        df['Result'] = df['Profit (USD)'].apply(lambda x: 'Win' if x > 0 else 'Loss')
    
    df['Close Time'] = pd.to_datetime(df['Close Time'])
    df_sorted = df.sort_values('Close Time')
    df_sorted['Cumulative_Profit'] = df_sorted['Profit (USD)'].cumsum()
    df_sorted['Trade_Number'] = range(1, len(df_sorted) + 1)
    
    # Calcular métricas clave
    total_trades = len(df)
    winning_trades = len(df[df['Result'] == 'Win'])
    losing_trades = len(df[df['Result'] == 'Loss'])
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    total_profit = df['Profit (USD)'].sum()
    avg_win = df[df['Result'] == 'Win']['Profit (USD)'].mean() if winning_trades > 0 else 0
    avg_loss = df[df['Result'] == 'Loss']['Profit (USD)'].mean() if losing_trades > 0 else 0
    profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else 0
    
    # Calcular drawdown
    running_max = df_sorted['Cumulative_Profit'].expanding().max()
    drawdown = df_sorted['Cumulative_Profit'] - running_max
    max_drawdown = drawdown.min()
    
    # Dashboard de métricas principales
    st.markdown("---")
    st.subheader("📈 Métricas Principales")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="💰 Profit Total",
            value=f"${total_profit:,.2f}",
            delta=f"{total_profit:+.2f}" if total_profit != 0 else None
        )
    
    with col2:
        st.metric(
            label="🎯 Win Rate",
            value=f"{win_rate:.1f}%",
            delta=f"{win_rate-50:.1f}%" if win_rate != 50 else None
        )
    
    with col3:
        st.metric(
            label="📊 Total Trades",
            value=f"{total_trades:,}",
            delta=f"+{total_trades}" if total_trades > 0 else None
        )
    
    with col4:
        st.metric(
            label="📉 Max Drawdown",
            value=f"${max_drawdown:,.2f}",
            delta=f"{max_drawdown:+.2f}" if max_drawdown != 0 else None
        )
    
    with col5:
        st.metric(
            label="⚡ Profit Factor",
            value=f"{profit_factor:.2f}",
            delta=f"{profit_factor-1:+.2f}" if profit_factor != 1 else None
        )
    
    # Segunda fila de métricas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("✅ Trades Ganadores", f"{winning_trades:,}")
    
    with col2:
        st.metric("❌ Trades Perdedores", f"{losing_trades:,}")
    
    with col3:
        st.metric("💚 Ganancia Promedio", f"${avg_win:,.2f}")
    
    with col4:
        st.metric("💔 Pérdida Promedio", f"${avg_loss:,.2f}")
    
    st.markdown("---")
    
    # Gráfico de evolución del capital (mejorado)
    st.subheader("📈 Evolución del Capital")
    
    fig_capital = go.Figure()
    
    # Línea principal del capital
    fig_capital.add_trace(go.Scatter(
        x=df_sorted['Close Time'],
        y=df_sorted['Cumulative_Profit'],
        mode='lines',
        name='Capital Acumulado',
        line=dict(color='#3b82f6', width=3),
        fill='tonexty',
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))
    
    # Línea de drawdown
    fig_capital.add_trace(go.Scatter(
        x=df_sorted['Close Time'],
        y=running_max,
        mode='lines',
        name='Máximo Histórico',
        line=dict(color='#10b981', width=2, dash='dash'),
        opacity=0.7
    ))
    
    fig_capital.update_layout(
        title="Evolución del Capital y Drawdown",
        xaxis_title="Fecha",
        yaxis_title="Profit Acumulado ($)",
        height=500,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_capital, use_container_width=True)
    
    # Gráfico de distribución de ganancias/pérdidas
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribución de Resultados")
        
        # Histograma de profits
        fig_dist = px.histogram(
            df, 
            x='Profit (USD)', 
            nbins=30,
            title="Distribución de Ganancias/Pérdidas",
            color_discrete_sequence=['#3b82f6']
        )
        
        fig_dist.add_vline(x=0, line_dash="dash", line_color="red", annotation_text="Breakeven")
        fig_dist.update_layout(
            xaxis_title="Profit ($)",
            yaxis_title="Frecuencia",
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Win/Loss Ratio")
        
        # Pie chart de win/loss
        win_loss_counts = df['Result'].value_counts()
        colors = ['#10b981' if x == 'Win' else '#ef4444' for x in win_loss_counts.index]
        
        fig_pie = px.pie(
            values=win_loss_counts.values,
            names=win_loss_counts.index,
            title="Proporción de Trades Ganadores vs Perdedores",
            color_discrete_sequence=colors
        )
        
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Análisis por símbolo
    st.subheader("📈 Análisis por Símbolo")
    
    symbol_analysis = df.groupby('Symbol').agg({
        'Profit (USD)': ['sum', 'mean', 'count'],
        'Result': lambda x: (x == 'Win').mean()
    }).reset_index()
    
    symbol_analysis.columns = ['Symbol', 'Total_Profit', 'Avg_Profit', 'Total_Trades', 'Win_Rate']
    symbol_analysis = symbol_analysis.sort_values('Total_Profit', ascending=False)
    
    fig_symbol = px.bar(
        symbol_analysis.head(10),
        x='Symbol',
        y='Total_Profit',
        title="Top 10 Símbolos por Profit Total",
        color='Total_Profit',
        color_continuous_scale='RdYlGn'
    )
    
    fig_symbol.update_layout(
        xaxis_title="Símbolo",
        yaxis_title="Profit Total ($)",
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_symbol, use_container_width=True)
    
    # Análisis por día de la semana (mejorado)
    st.subheader("📅 Rendimiento por Día de la Semana")
    
    df['Day_of_Week'] = df['Close Time'].dt.dayofweek
    days = {0:'Lunes', 1:'Martes', 2:'Miércoles', 3:'Jueves', 4:'Viernes', 5:'Sábado', 6:'Domingo'}
    df['Day_Name'] = df['Day_of_Week'].map(days)
    
    day_analysis = df.groupby('Day_Name').agg({
        'Profit (USD)': ['sum', 'mean', 'count'],
        'Result': lambda x: (x == 'Win').mean()
    }).reset_index()
    
    day_analysis.columns = ['Día', 'Profit_Total', 'Profit_Promedio', 'Cantidad_Trades', 'Win_Rate']
    day_analysis['Día'] = pd.Categorical(day_analysis['Día'], categories=days.values(), ordered=True)
    day_analysis = day_analysis.sort_values('Día')
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_day_profit = px.bar(
            day_analysis,
            x='Día',
            y='Profit_Total',
            title="Profit Total por Día de la Semana",
            color='Profit_Total',
            color_continuous_scale='RdYlGn'
        )
        fig_day_profit.update_layout(height=400, template='plotly_white')
        st.plotly_chart(fig_day_profit, use_container_width=True)
    
    with col2:
        fig_day_winrate = px.bar(
            day_analysis,
            x='Día',
            y='Win_Rate',
            title="Win Rate por Día de la Semana",
            color='Win_Rate',
            color_continuous_scale='Blues'
        )
        fig_day_winrate.update_layout(height=400, template='plotly_white')
        st.plotly_chart(fig_day_winrate, use_container_width=True)
    
    # Análisis mensual (mejorado)
    st.subheader("📅 Análisis Mensual")
    
    df['Month-Year'] = df['Close Time'].dt.to_period('M').astype(str)
    monthly_results = df.groupby('Month-Year').agg({
        'Profit (USD)': ['sum', 'mean', 'count'],
        'Result': lambda x: (x == 'Win').mean()
    }).reset_index()
    
    monthly_results.columns = ['Mes', 'Total_Profit', 'Avg_Profit', 'Total_Trades', 'Win_Rate']
    
    fig_monthly = go.Figure()
    
    # Agregar barras con colores condicionales
    colors = ['#10b981' if x > 0 else '#ef4444' for x in monthly_results['Total_Profit']]
    
    fig_monthly.add_trace(go.Bar(
        x=monthly_results['Mes'],
        y=monthly_results['Total_Profit'],
        name='Profit Mensual',
        marker_color=colors,
        text=monthly_results['Total_Profit'].round(2),
        textposition='auto'
    ))
    
    fig_monthly.update_layout(
        title="Profit Mensual",
        xaxis_title="Mes",
        yaxis_title="Profit ($)",
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Tabla de resumen mensual
    st.subheader("📋 Resumen Mensual Detallado")
    
    # Formatear los datos para mejor visualización
    monthly_display = monthly_results.copy()
    monthly_display['Total_Profit'] = monthly_display['Total_Profit'].apply(lambda x: f"${x:,.2f}")
    monthly_display['Avg_Profit'] = monthly_display['Avg_Profit'].apply(lambda x: f"${x:,.2f}")
    monthly_display['Win_Rate'] = monthly_display['Win_Rate'].apply(lambda x: f"{x:.1%}")
    
    st.dataframe(
        monthly_display,
        column_config={
            "Mes": "Mes",
            "Total_Profit": "Profit Total",
            "Avg_Profit": "Profit Promedio",
            "Total_Trades": "Total Trades",
            "Win_Rate": "Win Rate"
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Estadísticas adicionales
    st.subheader("📊 Estadísticas Adicionales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📏 Duración Promedio", f"{df['Duration (hours)'].mean():.2f} horas")
        st.metric("⏱️ Duración Máxima", f"{df['Duration (hours)'].max():.2f} horas")
    
    with col2:
        best_trade = df.loc[df['Profit (USD)'].idxmax()]
        st.metric("🏆 Mejor Trade", f"${best_trade['Profit (USD)']:,.2f}")
        st.caption(f"Símbolo: {best_trade['Symbol']}")
    
    with col3:
        worst_trade = df.loc[df['Profit (USD)'].idxmin()]
        st.metric("📉 Peor Trade", f"${worst_trade['Profit (USD)']:,.2f}")
        st.caption(f"Símbolo: {worst_trade['Symbol']}")
    
    # Botón de descarga
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Descargar Datos")
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📄 Descargar CSV",
        data=csv_data,
        file_name=f'trading_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mime='text/csv'
    )

else:
    st.info("🚀 Por favor suba un archivo CSV o ingrese trades manualmente para comenzar el análisis.")
    
    # Mostrar algunos ejemplos de análisis que se pueden realizar
    st.subheader("🎯 Análisis Disponibles")
    
    features = [
        "📈 Evolución del capital en tiempo real",
        "📊 Distribución de ganancias y pérdidas",
        "🎯 Win Rate y métricas de rendimiento",
        "📅 Análisis por día de la semana",
        "📆 Resultados mensuales detallados",
        "📉 Cálculo de drawdown máximo",
        "🏆 Identificación de mejores y peores trades",
        "📋 Análisis por símbolo/instrumento",
        "⚡ Profit Factor y ratios de riesgo"
    ]
    
    for feature in features:
        st.markdown(f"• {feature}")
