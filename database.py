import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime
import os

DB_NAME = "trading_journal.db"

def init_database():
    """Inicializa la base de datos y crea las tablas necesarias"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            commission REAL DEFAULT 0,
            pnl REAL DEFAULT 0,
            strategy TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_trades_to_db(df):
    """Guarda el DataFrame de trades en la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM trades")
    df.to_sql('trades', conn, if_exists='append', index=False)
    
    conn.commit()
    conn.close()
    
    return True

def load_trades_from_db():
    """Carga los trades desde la base de datos"""
    if not os.path.exists(DB_NAME):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_NAME)
    
    try:
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY date DESC", conn)
        return df
    except pd.errors.DatabaseError:
        return pd.DataFrame()
    finally:
        conn.close()

def add_single_trade(date, symbol, side, quantity, price, commission=0, pnl=0, strategy="", notes=""):
    """Añade una operación individual a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO trades (date, symbol, side, quantity, price, commission, pnl, strategy, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, symbol, side, quantity, price, commission, pnl, strategy, notes))
    
    conn.commit()
    conn.close()
    
    return True

def delete_trade(trade_id):
    """Elimina una operación específica"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
    
    conn.commit()
    conn.close()
    
    return True

def get_trade_statistics():
    """Obtiene estadísticas básicas de las operaciones"""
    conn = sqlite3.connect(DB_NAME)
    
    try:
        total_trades = pd.read_sql_query("SELECT COUNT(*) as count FROM trades", conn).iloc[0]['count']
        total_pnl = pd.read_sql_query("SELECT SUM(pnl) as total FROM trades", conn).iloc[0]['total'] or 0
        winners = pd.read_sql_query("SELECT COUNT(*) as count FROM trades WHERE pnl > 0", conn).iloc[0]['count']
        losers = pd.read_sql_query("SELECT COUNT(*) as count FROM trades WHERE pnl < 0", conn).iloc[0]['count']
        best_trade = pd.read_sql_query("SELECT MAX(pnl) as best FROM trades", conn).iloc[0]['best'] or 0
        worst_trade = pd.read_sql_query("SELECT MIN(pnl) as worst FROM trades", conn).iloc[0]['worst'] or 0
        
        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'winners': winners,
            'losers': losers,
            'win_rate': (winners / total_trades * 100) if total_trades > 0 else 0,
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }
        
    except Exception as e:
        st.error(f"Error al obtener estadísticas: {e}")
        return None
    finally:
        conn.close()

def export_to_csv():
    """Exporta todos los datos a CSV"""
    df = load_trades_from_db()
    if not df.empty:
        csv_name = f"trades_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_name, index=False)
        return csv_name
    return None
