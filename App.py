import streamlit as st
import pandas as pd
from datetime import datetime
import time

st.title("📊 Análisis de Trades en Tiempo Real")

# Initialize session state for storing trades if it doesn't exist
if 'trades_df' not in st.session_state:
    st.session_state.trades_df = pd.DataFrame()

# Tab layout for different input methods
tab1, tab2 = st.tabs(["📤 Subir CSV", "✏️ Ingresar Manualmente"])

with tab1:
    # 1. CSV Upload functionality
    st.subheader("Subir archivo CSV de trades")
    archivo = st.file_uploader("Arrastra tu archivo CSV aquí", type="csv", key="csv_uploader")
    
    if archivo:
        try:
            # Process CSV data
            df = pd.read_csv(archivo)
            df = df[df['Profit (USD)'] != 0]
            df['Duration (hours)'] = (pd.to_datetime(df['Close Time']) - pd.to_datetime(df['Open Time'])).dt.total_seconds() / 3600
            df['Result'] = df['Profit (USD)'].apply(lambda x: 'Win' if x > 0 else 'Loss')
            
            # Remove 'Order ID' column if it exists
            if 'Order ID' in df.columns:
                df = df.drop(columns=['Order ID'])
            
            # Store in session state
            st.session_state.trades_df = df
            st.success("Datos cargados correctamente desde CSV!")
            
        except Exception as e:
            st.error(f"Error al procesar el archivo CSV: {str(e)}")

with tab2:
    # 2. Manual trade entry form
    st.subheader("Ingresar Trade Manualmente")
    
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
        
        submitted = st.form_submit_button("Agregar Trade")
        
        if submitted:
            if symbol and price > 0 and size > 0:
                # Create a new trade entry
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
                    'Close Time': f"{trade_date} {trade_time}",  # Using same as open time for simplicity
                    'Take Profit': None,  # Can be added to form if needed
                    'Stop Loss': None     # Can be added to form if needed
                }
                
                # Convert to DataFrame and append to existing data
                new_trade_df = pd.DataFrame([new_trade])
                
                if st.session_state.trades_df.empty:
                    st.session_state.trades_df = new_trade_df
                else:
                    st.session_state.trades_df = pd.concat([st.session_state.trades_df, new_trade_df], ignore_index=True)
                
                st.success("Trade agregado exitosamente!")
                time.sleep(1)
                st.rerun()
            else:
                st.warning("Por favor complete los campos requeridos (Symbol, Size, Price)")

# Display data and analysis only if we have trades
if not st.session_state.trades_df.empty:
    df = st.session_state.trades_df
    
    # Calculate additional metrics if not already present
    if 'Duration (hours)' not in df.columns:
        df['Duration (hours)'] = (pd.to_datetime(df['Close Time']) - pd.to_datetime(df['Open Time'])).dt.total_seconds() / 3600
    
    if 'Result' not in df.columns:
        df['Result'] = df['Profit (USD)'].apply(lambda x: 'Win' if x > 0 else 'Loss')
    
    # 3. Show data and analysis
    st.subheader("📋 Tabla de Trades Completa")
    st.dataframe(df)  # Show DataFrame as interactive table
    
    st.subheader("📊 Trades Ganados vs Perdidos")
    st.bar_chart(df['Result'].value_counts())  # Bar chart
    
    # 5. Monthly Profit/Loss Analysis
st.subheader("📅 Resultados Mensuales")

# Extract month and year from Close Time
df['Close Time'] = pd.to_datetime(df['Close Time'])
df['Month-Year'] = df['Close Time'].dt.to_period('M').astype(str)

# Calculate monthly profit
monthly_results = df.groupby('Month-Year')['Profit (USD)'].sum().reset_index()
monthly_results['Result'] = monthly_results['Profit (USD)'].apply(lambda x: 'Positivo' if x > 0 else 'Negativo')

# Create bar chart
st.bar_chart(monthly_results.set_index('Month-Year')['Profit (USD)'])

# Display monthly summary table with colored results
st.write("Resumen Mensual:")

# Create a styled DataFrame for display
def color_result(val):
    color = 'green' if val == 'Positivo' else 'red'
    return f'color: {color}'

styled_monthly = monthly_results.style.applymap(color_result, subset=['Result'])
st.dataframe(styled_monthly)
    
    # 4. Interactive filters
    st.sidebar.subheader("🔍 Filtros")
    symbol_filter = st.sidebar.selectbox("Filtrar por símbolo:", df['Symbol'].unique())
    filtered_df = df[df['Symbol'] == symbol_filter]
    st.write(f"Trades filtrados para {symbol_filter}:")
    st.dataframe(filtered_df)
    
    # Download button for the combined data
    st.sidebar.download_button(
        label="Descargar todos los trades",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='combined_trades.csv',
        mime='text/csv'
    )
else:
    st.info("Por favor suba un archivo CSV o ingrese trades manualmente para comenzar el análisis.")
