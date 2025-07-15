import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

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

# Inicializar datos en session_state
if 'trades_df' not in st.session_state:
    st.session_state.trades_df = pd.DataFrame()

# Sidebar
st.sidebar.header("⚙️ Configuraciones")

# Pestañas para entrada de datos
tab1, tab2 = st.tabs(["📤 Subir CSV", "✏️ Ingresar Manualmente"])

with tab1:
    st.subheader("📁 Subir archivo CSV de trades")
    archivo = st.file_uploader("Arrastra tu archivo CSV aquí", type="csv")
    
    if archivo:
        try:
            df = pd.read_csv(archivo)
            df = df[df['Profit (USD)'] != 0]
            df['Duration (hours)'] = (pd.to_datetime(df['Close Time']) - pd.to_datetime(df['Open Time'])).dt.total_seconds() / 3600
            df['Result'] = df['Profit (USD)'].apply(lambda x: 'Win' if x > 0 else 'Loss')
            
            if 'Order ID' in df.columns:
                df = df.drop(columns=['Order ID'])
            
            st.session_state.trades_df = df
            st.success("✅ Datos cargados correctamente!")
            
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

# Análisis (se mantienen igual todos tus gráficos y métricas)
if not st.session_state.trades_df.empty:
    df = st.session_state.trades_df.copy()
    
    # Preparar datos (igual que antes)
    if 'Duration (hours)' not in df.columns:
        df['Duration (hours)'] = (pd.to_datetime(df['Close Time']) - pd.to_datetime(df['Open Time'])).dt.total_seconds() / 3600
    
    if 'Result' not in df.columns:
        df['Result'] = df['Profit (USD)'].apply(lambda x: 'Win' if x > 0 else 'Loss')
    
    # ... (todo el resto de tu código de gráficos y métricas permanece igual)

else:
    st.info("🚀 Sube un archivo CSV o ingresa trades manualmente para comenzar.")

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
