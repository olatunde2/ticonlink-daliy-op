import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = Path('data/trades.db')

def init_database():
    """Initialize the database schema"""
    DB_PATH.parent.mkdir(exist_ok=True)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_calculator_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                trade_date TEXT NOT NULL,
                market_cycle_date TEXT,
                ticker TEXT NOT NULL,
                direction TEXT NOT NULL,
                scenario TEXT NOT NULL,
                description TEXT,
                
                -- Price calculations
                target_price_formula TEXT,
                target_price_value REAL,
                option_bid REAL,
                option_ask REAL,
                option_mid REAL,
                option_formula TEXT,
                
                -- Values
                intrinsic_value REAL,
                extrinsic_value REAL,
                target_size REAL,
                
                -- Formulas for display
                iv_formula TEXT,
                ev_formula TEXT,
                
                -- Status
                tradable_flag BOOLEAN,
                
                -- Additional metadata
                notes TEXT,
                
                -- Original inputs (JSON)
                inputs_json TEXT
            )
        ''')
        
        conn.commit()
        logging.info("✓ Database initialized at data/trades.db")

@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def insert_trade_result(
    trade_date,
    ticker,
    direction,
    scenario,
    target_price_value,
    option_bid,
    option_ask,
    intrinsic_value,
    extrinsic_value,
    target_size,
    tradable_flag,
    inputs_dict,
    market_cycle_date=None,
    description=None
):
    """Insert a new trade calculation result"""
    
    # Calculate option mid
    option_mid = (option_bid + option_ask) / 2
    
    # Build formulas for display
    target_price_formula = f"{inputs_dict.get('current_price', 0):.2f} - {target_size:.2f} = {target_price_value:.2f}"
    option_formula = f"{option_bid:.2f} + {option_ask:.2f} = {option_bid + option_ask:.2f}\n{option_bid + option_ask:.2f}/2 = {option_mid:.2f}"
    iv_formula = f"IV = {intrinsic_value:.2f}"
    ev_formula = f"{option_mid:.2f} - {intrinsic_value:.2f} = {extrinsic_value:.2f}"
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO trade_calculator_results (
                trade_date, market_cycle_date, ticker, direction, scenario,
                description, target_price_formula, target_price_value,
                option_bid, option_ask, option_mid, option_formula,
                intrinsic_value, extrinsic_value, target_size,
                iv_formula, ev_formula, tradable_flag, inputs_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_date, market_cycle_date, ticker, direction, scenario,
            description, target_price_formula, target_price_value,
            option_bid, option_ask, option_mid, option_formula,
            intrinsic_value, extrinsic_value, target_size,
            iv_formula, ev_formula, tradable_flag, json.dumps(inputs_dict)
        ))
        
        conn.commit()
        trade_id = cursor.lastrowid
        
        logging.info(f"✓ Saved trade result #{trade_id} for {ticker} {direction}")
        return trade_id

def fetch_recent_results(limit=20):
    """Fetch recent trade calculation results"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM trade_calculator_results
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'created_at': row['created_at'],
                'trade_date': row['trade_date'],
                'market_cycle_date': row['market_cycle_date'],
                'ticker': row['ticker'],
                'direction': row['direction'],
                'scenario': row['scenario'],
                'description': row['description'],
                'target_price_formula': row['target_price_formula'],
                'target_price_value': row['target_price_value'],
                'option_bid': row['option_bid'],
                'option_ask': row['option_ask'],
                'option_mid': row['option_mid'],
                'option_formula': row['option_formula'],
                'intrinsic_value': row['intrinsic_value'],
                'extrinsic_value': row['extrinsic_value'],
                'target_size': row['target_size'],
                'iv_formula': row['iv_formula'],
                'ev_formula': row['ev_formula'],
                'tradable_flag': bool(row['tradable_flag']),
                'inputs_json': row['inputs_json']
            })
        
        return results

def delete_trade_result(trade_id):
    """Delete a trade result by ID"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM trade_calculator_results WHERE id = ?', (trade_id,))
        conn.commit()
        logging.info(f"✓ Deleted trade result #{trade_id}")

def get_all_tickers():
    """Get unique list of all tickers in database"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT ticker FROM trade_calculator_results ORDER BY ticker')
        return [row[0] for row in cursor.fetchall()]
