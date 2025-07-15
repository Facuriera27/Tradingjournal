import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# 🔥 IMPORTANTE: Importamos nuestras funciones de base de datos
from database import (
    init_database, 
    save_trades_to_db, 
    load_trades_from_db,
    add_single_trade,
    delete_trade,
    get_trade_statistics,
    export_to_csv
)

# 🏗️ Configuración inicial
st.set_page_config(page_title="Trading Journal", layout="wide")

# 🎯 Inicializamos la base de datos al inicio
init_database()

def main():
    st.title("📊 Trading Journal - Con Base de Datos")
    st.markdown("---")
    
    # 📱 Sidebar para opciones
    st.sidebar.title("🔧 Opciones")
    
    # 📤 Sección para subir CSV
    st.sidebar.subheader("📁 Subir Datos")
    uploaded_file = st.sidebar.file_uploader("Selecciona tu archivo CSV", type=['csv'])
    
    if uploaded_file is not None:
        # 👀 Mostramos vista previa
        df_uploaded = pd.read_csv(uploaded_file)
        st.sidebar.write("Vista previa:")
        st.sidebar.dataframe(df_uploaded.head(3))
        
        # 💾 Botón para guardar en base de datos
        if st.sidebar.button("💾 Guardar en Base de Datos"):
            try:
                save_trades_to_db(df_uploaded)
                st.sidebar.success("¡Datos guardados exitosamente!")
                st.rerun()  # Recarga la página para mostrar los nuevos datos
            except Exception as e:
                st.sidebar.error(f"Error al guardar: {e}")
    
    # ➕ Sección para añadir operación manual
    with st.sidebar.expander("➕ Añadir Operación Manual"):
        with st.form("add_trade_form"):
            date = st.date_input("📅 Fecha")
            symbol = st.text_input("🏷️ Símbolo", placeholder="AAPL, TSLA, etc.")
            side = st.selectbox("📈 Lado", ["BUY", "SELL"])
            quantity = st.number_input("📦 Cantidad", min_value=0.0, step=0.1)
            price = st.number_input("💰 Precio", min_value=0.0, step=0.01)
            commission = st.number_input("💸 Comisión", min_value=0.0, value=0.0, step=0.01)
            pnl = st.number_input("📊 PnL", value=0.0, step=0.01)
            strategy = st.text_input("🎯 Estrategia", placeholder="Opcional")
            notes = st.text_area("📝 Notas", placeholder="Opcional")
            
            submitted = st.form_submit_button("➕ Añadir Operación")
            
            if submitted:
                if symbol and quantity > 0 and price > 0:
                    try:
                        add_single_trade(date, symbol, side, quantity, price, commission, pnl, strategy, notes)
                        st.success("¡Operación añadida exitosamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al añadir operación: {e}")
                else:
                    st.error("Por favor completa los campos obligatorios")
    
    # 📊 Sección de exportación
    st.sidebar.subheader("📤 Exportar Datos")
    if st.sidebar.button("📄 Exportar a CSV"):
        csv_file = export_to_csv()
        if csv_file:
            st.sidebar.success(f"✅ Archivo creado: {csv_file}")
            # Aquí podrías añadir un botón de descarga si lo necesitas
        else:
            st.sidebar.warning("No hay datos para exportar")
    
    # 🔄 Botón para recargar datos
    if st.sidebar.button("🔄 Recargar Datos"):
        st.rerun()
    
    # 📊 CONTENIDO PRINCIPAL
    st.header("📈 Datos Actuales")
    
    # 📖 Cargamos los datos desde la base de datos
    df = load_trades_from_db()
    
    if df.empty:
        st.info("🔍 No hay operaciones guardadas. Sube un CSV o añade operaciones manualmente.")
        return
    
    # 📊 Mostramos estadísticas
    st.subheader("📊 Estadísticas Generales")
    stats = get_trade_statistics()
    
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Total Operaciones", stats['total_trades'])
        with col2:
            st.metric("💰 PnL Total", f"${stats['total_pnl']:.2f}")
        with col3:
            st.metric("✅ Tasa de Éxito", f"{stats['win_rate']:.1f}%")
        with col4:
            st.metric("🏆 Mejor Operación", f"${stats['best_trade']:.2f}")
        
        # Segunda fila de métricas
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric("😊 Ganadoras", stats['winners'])
        with col6:
            st.metric("😢 Perdedoras", stats['losers'])
        with col7:
            st.metric("📉 Peor Operación", f"${stats['worst_trade']:.2f}")
        with col8:
            if stats['total_trades'] > 0:
                avg_pnl = stats['total_pnl'] / stats['total_trades']
                st.metric("📊 PnL Promedio", f"${avg_pnl:.2f}")
    
    st.markdown("---")
    
    # 📋 Tabla de operaciones
    st.subheader("📋 Todas las Operaciones")
    
    # 🔍 Filtros opcionales
    col1, col2 = st.columns(2)
    
    with col1:
        symbols = df['symbol'].unique() if 'symbol' in df.columns else []
        selected_symbols = st.multiselect("🔍 Filtrar por símbolo", symbols, default=symbols)
    
    with col2:
        sides = df['side'].unique() if 'side' in df.columns else []
        selected_sides = st.multiselect("🔍 Filtrar por lado", sides, default=sides)
    
    # Aplicar filtros
    filtered_df = df.copy()
    if selected_symbols:
        filtered_df = filtered_df[filtered_df['symbol'].isin(selected_symbols)]
    if selected_sides:
        filtered_df = filtered_df[filtered_df['side'].isin(selected_sides)]
    
    # Mostrar tabla filtrada
    st.dataframe(filtered_df, use_container_width=True)
    
    # 📊 Gráficos
    if not filtered_df.empty and 'pnl' in filtered_df.columns:
        st.subheader("📈 Gráficos")
        
        tab1, tab2, tab3 = st.tabs(["📊 PnL por Operación", "📈 PnL Acumulado", "🥧 Distribución por Símbolo"])
        
        with tab1:
            # Gráfico de barras del PnL
            fig_bar = px.bar(
                filtered_df, 
                x=filtered_df.index, 
                y='pnl',
                title="PnL por Operación",
                color='pnl',
                color_continuous_scale=['red', 'green']
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with tab2:
            # Gráfico de PnL acumulado
            filtered_df_sorted = filtered_df.sort_values('date' if 'date' in filtered_df.columns else filtered_df.columns[0])
            filtered_df_sorted['pnl_cumulative'] = filtered_df_sorted['pnl'].cumsum()
            
            fig_line = px.line(
                filtered_df_sorted, 
                x='date' if 'date' in filtered_df_sorted.columns else filtered_df_sorted.index,
                y='pnl_cumulative',
                title="PnL Acumulado"
            )
            st.plotly_chart(fig_line, use_container_width=True)
        
        with tab3:
            # Gráfico de distribución por símbolo
            if 'symbol' in filtered_df.columns:
                symbol_pnl = filtered_df.groupby('symbol')['pnl'].sum().reset_index()
                fig_pie = px.pie(
                    symbol_pnl, 
                    values='pnl', 
                    names='symbol',
                    title="Distribución de PnL por Símbolo"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
    
    # 🗑️ Sección para eliminar operaciones (opcional)
    if not df.empty:
        st.subheader("🗑️ Eliminar Operación")
        
        # Crear lista de operaciones para seleccionar
        operation_options = []
        for _, row in df.iterrows():
            if 'id' in row and 'symbol' in row and 'date' in row:
                operation_options.append(f"ID: {row['id']} - {row['symbol']} - {row['date']}")
        
        if operation_options:
            selected_operation = st.selectbox("Selecciona operación a eliminar", [""] + operation_options)
            
            if selected_operation:
                operation_id = int(selected_operation.split(" - ")[0].replace("ID: ", ""))
                
                if st.button("🗑️ Eliminar Operación Seleccionada"):
                    try:
                        delete_trade(operation_id)
                        st.success("¡Operación eliminada exitosamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar operación: {e}")

if __name__ == "__main__":
    main()
