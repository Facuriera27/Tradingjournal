import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import calendar

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
    .calendar-container {
        background: #1a1a1a;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
    }
    .calendar-header {
        text-align: center;
        color: white;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 5px;
        max-width: 800px;
        margin: 0 auto;
    }
    .calendar-day-header {
        text-align: center;
        color: #888;
        font-weight: bold;
        padding: 10px;
        font-size: 0.9rem;
    }
    .calendar-day {
        aspect-ratio: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border-radius: 8px;
        min-height: 80px;
        position: relative;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .calendar-day:hover {
        transform: scale(1.05);
        z-index: 10;
    }
    .day-number {
        font-size: 1.1rem;
        font-weight: bold;
        color: white;
        margin-bottom: 5px;
    }
    .day-profit {
        font-size: 0.8rem;
        font-weight: bold;
        color: white;
    }
    .day-trades {
        font-size: 0.7rem;
        color: #ccc;
    }
    .positive-day {
        background: linear-gradient(135deg, #10b981, #059669);
        border: 1px solid #10b981;
    }
    .negative-day {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        border: 1px solid #ef4444;
    }
    .neutral-day {
        background: #2a2a2a;
        border: 1px solid #404040;
    }
    .empty-day {
        background: transparent;
    }
    .monthly-stats {
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
        flex-wrap: wrap;
    }
    .stat-item {
        text-align: center;
        color: white;
        padding: 10px;
        background: #2a2a2a;
        border-radius: 8px;
        margin: 5px;
        min-width: 120px;
    }
    .stat-value {
        font-size: 1.2rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

def create_trading_calendar(df, year, month):
    """Crea un calendario de trading para un mes específico"""
    
    # Filtrar datos del mes
    df['Date'] = pd.to_datetime(df['Close Time']).dt.date
    month_df = df[
        (pd.to_datetime(df['Close Time']).dt.year == year) & 
        (pd.to_datetime(df['Close Time']).dt.month == month)
    ]
    
    # Agrupar por día
    daily_stats = month_df.groupby('Date').agg({
        'Profit (USD)': ['sum', 'count']
    }).round(2)
    
    daily_stats.columns = ['profit', 'trades']
    daily_stats = daily_stats.reset_index()
    
    # Configurar calendario
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # Estadísticas del mes
    total_profit = month_df['Profit (USD)'].sum()
    total_trades = len(month_df)
    winning_days = len(daily_stats[daily_stats['profit'] > 0])
    losing_days = len(daily_stats[daily_stats['profit'] < 0])
    
    # HTML del calendario
    calendar_html = f"""
    <div class="calendar-container">
        <div class="calendar-header">{month_name} {year}</div>
        
        <div class="monthly-stats">
            <div class="stat-item">
                <div class="stat-value" style="color: {'#10b981' if total_profit >= 0 else '#ef4444'}">${total_profit:,.2f}</div>
                <div class="stat-label">Monthly P&L</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{total_trades}</div>
                <div class="stat-label">Total Trades</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" style="color: #10b981">{winning_days}</div>
                <div class="stat-label">Winning Days</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" style="color: #ef4444">{losing_days}</div>
                <div class="stat-label">Losing Days</div>
            </div>
        </div>
        
        <div class="calendar-grid">
            <div class="calendar-day-header">Sun</div>
            <div class="calendar-day-header">Mon</div>
            <div class="calendar-day-header">Tue</div>
            <div class="calendar-day-header">Wed</div>
            <div class="calendar-day-header">Thu</div>
            <div class="calendar-day-header">Fri</div>
            <div class="calendar-day-header">Sat</div>
    """
    
    for week in cal:
        for day in week:
            if day == 0:
                calendar_html += '<div class="calendar-day empty-day"></div>'
            else:
                date_obj = datetime(year, month, day).date()
                day_data = daily_stats[daily_stats['Date'] == date_obj]
                
                if not day_data.empty:
                    profit = day_data.iloc[0]['profit']
                    trades = int(day_data.iloc[0]['trades'])
                    
                    if profit > 0:
                        day_class = "positive-day"
                    elif profit < 0:
                        day_class = "negative-day"
                    else:
                        day_class = "neutral-day"
                    
                    calendar_html += f"""
                    <div class="calendar-day {day_class}" title="Día {day}: ${profit:,.2f} ({trades} trades)">
                        <div class="day-number">{day}</div>
                        <div class="day-profit">${profit:,.0f}</div>
                        <div class="day-trades">{trades} trades</div>
                    </div>
                    """
                else:
                    calendar_html += f"""
                    <div class="calendar-day neutral-day">
                        <div class="day-number">{day}</div>
                    </div>
                    """
    
    calendar_html += """
        </div>
    </div>
    """
    
    return calendar_html

st.markdown('<h1 class="main-header">📊 Trading Analytics Dashboard</h1>', unsafe_allow_html=True)

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
    
    # NUEVO: Calendario de Trading
    st.markdown("---")
    st.subheader("📅 Calendario de Trading")
    
    # Selector de mes y año para el calendario
    col1, col2 = st.columns([1, 3])
    with col1:
        # Obtener años disponibles en los datos
        available_years = sorted(df['Close Time'].dt.year.unique())
        if available_years:
            selected_year = st.selectbox("Año", available_years, index=len(available_years)-1)
            
            # Obtener meses disponibles para el año seleccionado
            year_data = df[df['Close Time'].dt.year == selected_year]
            available_months = sorted(year_data['Close Time'].dt.month.unique())
            
            if available_months:
                month_names = [calendar.month_name[m] for m in available_months]
                selected_month_name = st.selectbox("Mes", month_names, index=len(month_names)-1)
                selected_month = available_months[month_names.index(selected_month_name)]
                
                # Generar y mostrar el calendario
                calendar_html = create_trading_calendar(df, selected_year, selected_month)
                st.markdown(calendar_html, unsafe_allow_html=True)
    
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
