import streamlit as st
import pandas as pd
from datetime import datetime
import time
import numpy as np

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
                    'Close Time': f"{trade_date} {trade_time}",
                    'Take Profit': None,
                    'Stop Loss': None
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

# Display analysis only if we have trades
if not st.session_state.trades_df.empty:
    df = st.session_state.trades_df
    
    # Calculate additional metrics if not already present
    if 'Duration (hours)' not in df.columns:
        df['Duration (hours)'] = (pd.to_datetime(df['Close Time']) - pd.to_datetime(df['Open Time'])).dt.total_seconds() / 3600
    
    if 'Result' not in df.columns:
        df['Result'] = df['Profit (USD)'].apply(lambda x: 'Win' if x > 0 else 'Loss')
    
    # Ensure datetime format
    df['Close Time'] = pd.to_datetime(df['Close Time'])
    
    # 1. Análisis de Win/Loss a lo largo del tiempo
    st.subheader("📈 Evolución de Wins/Losses en el Tiempo")
    
    # Create a cumulative win/loss count
    df_sorted = df.sort_values('Close Time')
    df_sorted['Win_Cumulative'] = (df_sorted['Result'] == 'Win').cumsum()
    df_sorted['Loss_Cumulative'] = (df_sorted['Result'] == 'Loss').cumsum()
    
    # Plot cumulative wins/losses
    st.line_chart(df_sorted.set_index('Close Time')[['Win_Cumulative', 'Loss_Cumulative']])
    
    # 2. Evolución del capital
    st.subheader("💰 Evolución del Capital")
    
    # Calculate cumulative profit
    df_sorted['Cumulative_Profit'] = df_sorted['Profit (USD)'].cumsum()
    
    # Plot capital growth
    st.line_chart(df_sorted.set_index('Close Time')['Cumulative_Profit'])
    
    # 3. Análisis por día de la semana
    st.subheader("📅 Rendimiento por Día de la Semana")
    
    # Extract day of week (0=Monday, 6=Sunday)
    df['Day_of_Week'] = df['Close Time'].dt.dayofweek
    days = {0:'Lunes', 1:'Martes', 2:'Miércoles', 3:'Jueves', 4:'Viernes', 5:'Sábado', 6:'Domingo'}
    df['Day_Name'] = df['Day_of_Week'].map(days)
    
    # Group by day of week
    day_analysis = df.groupby('Day_Name').agg({
        'Profit (USD)': ['sum', 'mean', 'count'],
        'Result': lambda x: (x == 'Win').mean()  # Win rate
    }).reset_index()
    
    day_analysis.columns = ['Día', 'Profit Total', 'Profit Promedio', 'Cantidad Trades', 'Win Rate']
    
    # Sort by day of week (not alphabetically)
    day_analysis['Día'] = pd.Categorical(day_analysis['Día'], categories=days.values(), ordered=True)
    day_analysis = day_analysis.sort_values('Día')
    
    # Display metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Profit Total por Día:**")
        st.bar_chart(day_analysis.set_index('Día')['Profit Total'])
        
    with col2:
        st.write("**Win Rate por Día:**")
        st.bar_chart(day_analysis.set_index('Día')['Win Rate'])
    
    st.write("**Métricas Detalladas por Día:**")
    st.dataframe(day_analysis)
    
    # 4. Trades Ganados vs Perdidos (original)
    st.subheader("📊 Trades Ganados vs Perdidos (Global)")
    st.bar_chart(df['Result'].value_counts())
    
    # 5. Monthly Profit/Loss Analysis (original)
    st.subheader("📅 Resultados Mensuales")
    
    # Extract month and year
    df['Month-Year'] = df['Close Time'].dt.to_period('M').astype(str)
    
    # Calculate monthly profit
    monthly_results = df.groupby('Month-Year')['Profit (USD)'].sum().reset_index()
    monthly_results['Result'] = monthly_results['Profit (USD)'].apply(lambda x: 'Positivo' if x > 0 else 'Negativo')
    
    # Create bar chart
    st.bar_chart(monthly_results.set_index('Month-Year')['Profit (USD)'])
    
    # Display monthly summary table with colored results
    st.write("Resumen Mensual:")
    
    def color_result(val):
        color = 'green' if val == 'Positivo' else 'red'
        return f'color: {color}'
    
    styled_monthly = monthly_results.style.applymap(color_result, subset=['Result'])
    st.dataframe(styled_monthly)
    
    # Download button for the combined data
    st.sidebar.download_button(
        label="Descargar todos los trades",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='combined_trades.csv',
        mime='text/csv'
    )
else:
    st.info("Por favor suba un archivo CSV o ingrese trades manualmente para comenzar el análisis.")
