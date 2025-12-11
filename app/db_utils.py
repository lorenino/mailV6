import sqlite3
import pandas as pd
import os
import time
import functools

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, '..', 'data', 'clients.db')

# Retry decorator for database operations
def retry_on_lock(max_retries=3, delay=0.5):
    """Decorator to retry database operations if locked."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "locked" in str(e).lower():
                        last_error = e
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator

def get_db_connection():
    """Get a database connection with WAL mode and timeout."""
    conn = sqlite3.connect(
        DB_FILE, 
        timeout=30.0,  # Wait up to 30s if database is locked
        check_same_thread=False  # Allow multi-threaded access
    )
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for better concurrent access
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')  # 30 second busy timeout
    return conn

@retry_on_lock(max_retries=3, delay=0.5)
def get_unsent_clients():
    """Returns a list of clients where 'Envoyé ?' is NOT 'OUI'."""
    conn = get_db_connection()
    try:
        query = 'SELECT * FROM clients WHERE "Envoyé ?" != "OUI" OR "Envoyé ?" IS NULL'
        clients = conn.execute(query).fetchall()
        return [dict(row) for row in clients]
    finally:
        conn.close()

@retry_on_lock(max_retries=5, delay=1.0)
def mark_as_sent(client_id):
    """Updates 'Envoyé ?' to 'OUI' for a specific client ID."""
    conn = get_db_connection()
    try:
        conn.execute('UPDATE clients SET "Envoyé ?" = "OUI" WHERE id = ?', (client_id,))
        conn.commit()
    finally:
        conn.close()

def add_client(nom, prenom, email, societe, civilite='M.', provenance='Script'):
    """Adds a new client to the database."""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO clients (Provenance, Civilité, Nom, Prénom, "Société - Nom", "Email 1", "Envoyé ?") VALUES (?, ?, ?, ?, ?, ?, ?)',
        (provenance, civilite, nom, prenom, societe, email, 'NON')
    )
    conn.commit()
    conn.close()

@retry_on_lock(max_retries=3, delay=0.5)
def get_all_clients_df():
    """Returns all clients as a pandas DataFrame (useful for analysis)."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM clients", conn)
        return df
    finally:
        conn.close()

# Example usage for testing
if __name__ == "__main__":
    print("Testing db_utils...")
    unsent = get_unsent_clients()
    print(f"Found {len(unsent)} unsent clients.")
    if unsent:
        print(f"First unsent: {unsent[0]}")

# End of file
