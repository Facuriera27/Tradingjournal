import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# CSS personalizado
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
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">📊 Trading Analytics Dashboard</h1>', unsafe_allow_html=True)

# Función para crear el gráfico de calendario
def create_calendar_heatmap(df, selected_month=None):
    """
    Crea un gráfico de calendario mostrando profit diario y número de trades
    """
    # Preparar datos diarios
    df['Date'] = pd.to_datetime(df['Close Time']).dt.date
    daily_data = df.groupby('Date').agg({
        'Profit (USD)': ['sum', 'count']
    }).round(2)
    
    # Aplanar columnas
    daily_data.columns = ['Daily_Profit', 'Num_Trades']
    daily_data = daily_data.reset_index()
    
    # Filtrar por mes si se especifica
    if selected_month:
        daily_data = daily_data[pd.to_datetime(daily_data['Date']).dt.to_period('M') == selected_month]
    
    if daily_data.empty:
        return None
    
    # Preparar datos para el heatmap
    daily_data['Year'] = pd.to_datetime(daily_data['Date']).dt.year
    daily_data['Month'] = pd.to_datetime(daily_data['Date']).dt.month
    daily_data['Day'] = pd.to_datetime(daily_data['Date']).dt.day
    daily_data['Weekday'] = pd.to_datetime(daily_data['Date']).dt.day_name()
    daily_data['Week'] = pd.to_datetime(daily_data['Date']).dt.isocalendar().week
    
    # Mapear días de la semana
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_data['Weekday_num'] = daily_data['Weekday'].map({day: i for i, day in enumerate(weekdays)})
    
    # Crear texto para hover
    daily_data['Hover_text'] = daily_data.apply(lambda x: 
        f"Fecha: {x['Date']}<br>" +
        f"Profit: ${x['Daily_Profit']:,.2f}<br>" +
        f"Trades: {int(x['Num_Trades'])}<br>" +
        f"Promedio: ${x['Daily_Profit']/x['Num_Trades']:,.2f}",
        axis=1
    )
    
    # Crear el heatmap
    fig = go.Figure()
    
    # Configurar escala de colores
    max_abs_profit = max(abs(daily_data['Daily_Profit'].min()), abs(daily_data['Daily_Profit'].max()))
    
    fig.add_trace(go.Scatter(
        x=daily_data['Week'],
        y=daily_data['Weekday_num'],
        mode='markers+text',
        marker=dict(
            size=40,
            color=daily_data['Daily_Profit'],
            colorscale=[[0, '#ef4444'], [0.5, '#f3f4f6'], [1, '#10b981']],
            cmin=-max_abs_profit,
            cmax=max_abs_profit,
            showscale=True,
            colorbar=dict(
                title="Profit ($)",
                titleside="right"
            ),
            line=dict(width=1, color='white')
        ),
        text=daily_data['Num_Trades'].astype(str),
        textfont=dict(size=12, color='white'),
        hovertemplate='%{customdata}<extra></extra>',
        customdata=daily_data['Hover_text']
    ))
    
    fig.update_layout(
        title="📅 Calendario de Trading - Profit Diario y Número de Trades",
        xaxis=dict(
            title="Semana del Año",
            tickmode='linear',
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title="Día de la Semana",
            tickmode='array',
            tickvals=list(range(7)),
            ticktext=weekdays,
            showgrid=True,
            gridcolor='lightgray'
        ),
        height=400,
        showlegend=False,
        plot_bgcolor='white',
        font=dict(size=10)
    )
    
    return fig

# Inicializar datos en session_state
if 'trades_df' not in st.session_state:
    st.session_state.trades_df = pd.DataFrame()

# Sidebar
st.sidebar.header("⚙️ Configuraciones")

# Pestañas para entrada de datos
tab1, tab2 = st.tabs(["📤 Subir CSV", "✏️ Ingresar Manualmente"])

with tab1:
    st.subheader("📁 Subir archivo CSV de trades")
    archivo = st.file_uploader("Arrastra tu archivo CSV aquí", type="csv", key="csv_uploader")
    
    if archivo:
        try:
            df = pd.read_csv(archivo)
            
            # Verificación de columnas obligatorias
            required_columns = ['Profit (USD)', 'Close Time', 'Open Time']
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                st.error(f"❌ Faltan columnas obligatorias: {', '.join(missing)}")
            else:
                # Procesamiento de datos
                df = df[df['Profit (USD)'] != 0]
                df['Duration (hours)'] = (pd.to_datetime(df['Close Time']) - pd.to_datetime(df['Open Time'])).dt.total_seconds() / 3600
                df['Result'] = df['Profit (USD)'].apply(lambda x: 'Win' if x > 0 else 'Loss')
                
                if 'Order ID' in df.columns:
                    df = df.drop(columns=['Order ID'])
                
                st.session_state.trades_df = df
                st.success("✅ Datos cargados correctamente!")
                
                # Análisis mes a mes
                st.subheader("📅 Análisis Mes a Mes")
                
                # Preparar datos para análisis mensual
                df['Close Time'] = pd.to_datetime(df['Close Time'])
                df['Month'] = df['Close Time'].dt.to_period('M')
                
                # Agrupar por mes
                monthly_analysis = df.groupby('Month').agg({
                    'Profit (USD)': ['sum', 'count'],
                    'Result': lambda x: (x == 'Win').sum()
                }).round(2)
                
                # Aplanar columnas
                monthly_analysis.columns = ['Total_Profit', 'Total_Trades', 'Winning_Trades']
                monthly_analysis['Losing_Trades'] = monthly_analysis['Total_Trades'] - monthly_analysis['Winning_Trades']
                monthly_analysis['Win_Rate'] = (monthly_analysis['Winning_Trades'] / monthly_analysis['Total_Trades'] * 100).round(1)
                
                # Mostrar tabla con colores
                for month in monthly_analysis.index:
                    row = monthly_analysis.loc[month]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**{month}**")
                    
                    with col2:
                        profit_color = "🟢" if row['Total_Profit'] > 0 else "🔴"
                        st.write(f"{profit_color} ${row['Total_Profit']:,.2f}")
                    
                    with col3:
                        st.write(f"🟢 {int(row['Winning_Trades'])} | 🔴 {int(row['Losing_Trades'])}")
                    
                    with col4:
                        st.write(f"📊 {row['Win_Rate']:.1f}% WR")
                
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")

with tab2:
    st.subheader("✏️ Ingresar Trade Manualmente")
    
    with st.form("trade_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            market = st.selectbox("Market", ["STOCK", "FOREX", "CRYPTO", "FUTURES"])
            symbol = st.text_input("Symbol", "AAPL")
            action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
            
        with col2:
            trade_date = st.date_input("Date", datetime.now())
            trade_time = st.time_input("Time", datetime.now().time())
            size = st.number_input("Size", min_value=0.0, step=0.01)
            price = st.number_input("Price", min_value=0.0, step=0.0001)
        
        profit = st.number_input("Profit (USD)", step=0.01)
        
        submitted = st.form_submit_button("➕ Agregar Trade")
        
        if submitted:
            new_trade = {
                'Market': market,
                'Symbol': symbol.upper(),
                'Side': action,
                'Open Time': f"{trade_date} {trade_time}",
                'Size': size,
                'Open Price': price,
                'Profit (USD)': profit,
                'Close Time': f"{trade_date} {trade_time}",
                'Result': 'Win' if profit > 0 else 'Loss'
            }
            
            new_trade_df = pd.DataFrame([new_trade])
            st.session_state.trades_df = pd.concat([st.session_state.trades_df, new_trade_df], ignore_index=True)
            st.success("✅ Trade agregado!")
            time.sleep(1)
            st.rerun()

# Análisis y gráficos
if not st.session_state.trades_df.empty:
    df = st.session_state.trades_df.copy()
    
    # Debug: Mostrar información de los datos
    st.sidebar.write("ℹ️ Datos cargados:", len(df), "trades")
    
    # Preparar datos
    df['Close Time'] = pd.to_datetime(df['Close Time'])
    df['Open Time'] = pd.to_datetime(df['Open Time'])
    df['Duration (hours)'] = (df['Close Time'] - df['Open Time']).dt.total_seconds() / 3600
    df['Result'] = df['Profit (USD)'].apply(lambda x: 'Win' if x > 0 else 'Loss')
    df_sorted = df.sort_values('Close Time')
    df_sorted['Cumulative_Profit'] = df_sorted['Profit (USD)'].cumsum()
    df_sorted['Trade_Number'] = range(1, len(df_sorted) + 1)
    
    # Métricas clave
    st.markdown("---")
    st.subheader("📈 Métricas Principales")
    
    total_trades = len(df)
    winning_trades = len(df[df['Result'] == 'Win'])
    losing_trades = len(df[df['Result'] == 'Loss'])
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    total_profit = df['Profit (USD)'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Profit Total", f"${total_profit:,.2f}")
    col2.metric("🎯 Win Rate", f"{win_rate:.1f}%")
    col3.metric("📊 Total Trades", f"{total_trades:,}")
    col4.metric("✅ Trades Ganadores", f"{winning_trades:,}")
    
    # NUEVO: Gráfico de calendario mensual
    st.markdown("---")
    st.subheader("📅 Vista de Calendario - Trading Diario")
    
    # Selector de mes para el calendario
    df['Month_Period'] = pd.to_datetime(df['Close Time']).dt.to_period('M')
    available_months = sorted(df['Month_Period'].unique())
    
    if len(available_months) > 1:
        selected_month = st.selectbox(
            "Selecciona un mes para el calendario:",
            options=['Todos los meses'] + [str(month) for month in available_months],
            key="month_selector"
        )
        
        if selected_month != 'Todos los meses':
            selected_month = pd.Period(selected_month)
        else:
            selected_month = None
    else:
        selected_month = available_months[0] if available_months else None
    
    # Crear y mostrar el gráfico de calendario
    calendar_fig = create_calendar_heatmap(df, selected_month)
    if calendar_fig:
        st.plotly_chart(calendar_fig, use_container_width=True)
        
        # Información adicional del calendario
        st.info("""
        📋 **Cómo leer el gráfico de calendario:**
        - 🟢 **Verde**: Días con ganancias
        - 🔴 **Rojo**: Días con pérdidas  
        - **Números**: Cantidad de trades realizados ese día
        - **Hover**: Pasa el mouse para ver detalles del día
        """)
    
    # Gráfico de evolución del capital
    st.markdown("---")
    st.subheader("📈 Evolución del Capital")
    
    fig_capital = px.line(
        df_sorted,
        x='Close Time',
        y='Cumulative_Profit',
        title="Capital Acumulado",
        labels={'Cumulative_Profit': 'Profit Acumulado ($)', 'Close Time': 'Fecha'}
    )
    st.plotly_chart(fig_capital, use_container_width=True)
    
    # Gráfico de distribución de resultados
    st.subheader("📊 Distribución de Resultados")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_dist = px.histogram(
            df,
            x='Profit (USD)',
            nbins=20,
            title="Distribución de Ganancias/Pérdidas",
            color='Result',
            color_discrete_map={'Win': '#10b981', 'Loss': '#ef4444'}
        )
        st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        fig_pie = px.pie(
            df,
            names='Result',
            title="Win/Loss Ratio",
            color='Result',
            color_discrete_map={'Win': '#10b981', 'Loss': '#ef4444'}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Gráfico por símbolo
    if 'Symbol' in df.columns:
        st.subheader("📈 Rendimiento por Símbolo")
        symbol_profit = df.groupby('Symbol')['Profit (USD)'].sum().sort_values()
        fig_symbol = px.bar(
            symbol_profit,
            x=symbol_profit.values,
            y=symbol_profit.index,
            orientation='h',
            title="Profit por Símbolo",
            color=symbol_profit.values,
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig_symbol, use_container_width=True)

else:
    st.info("🚀 Sube un archivo CSV o ingresa trades manualmente para comenzar el análisis.")

# Botón para borrar datos
if st.sidebar.button("🧹 Borrar todos los datos"):
    st.session_state.trades_df = pd.DataFrame()
    st.sidebar.success("Datos borrados!")
    time.sleep(1)
    st.rerun()

# Botón de descarga
if not st.session_state.trades_df.empty:
    csv_data = st.session_state.trades_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📄 Descargar CSV",
        data=csv_data,
        file_name='trading_data.csv',
        mime='text/csv'
    )
