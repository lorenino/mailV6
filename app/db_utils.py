import sqlite3
import pandas as pd
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, '..', 'data', 'clients.db')

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_unsent_clients():
    """Returns a list of clients where 'Envoyé ?' is NOT 'OUI'."""
    conn = get_db_connection()
    # Note: Column names with spaces or special chars need quotes
    query = 'SELECT * FROM clients WHERE "Envoyé ?" != "OUI" OR "Envoyé ?" IS NULL'
    clients = conn.execute(query).fetchall()
    conn.close()
    return [dict(row) for row in clients]

def mark_as_sent(client_id):
    """Updates 'Envoyé ?' to 'OUI' for a specific client ID."""
    conn = get_db_connection()
    conn.execute('UPDATE clients SET "Envoyé ?" = "OUI" WHERE id = ?', (client_id,))
    conn.commit()
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

def get_all_clients_df():
    """Returns all clients as a pandas DataFrame (useful for analysis)."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM clients", conn)
    conn.close()
    return df

# Example usage for testing
if __name__ == "__main__":
    print("Testing db_utils...")
    unsent = get_unsent_clients()
    print(f"Found {len(unsent)} unsent clients.")
    if unsent:
        print(f"First unsent: {unsent[0]}")

# End of file
